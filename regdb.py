"""Shared helpers for the dummy Modbus server.

* parse_markdown / write_markdown : defaults file  <->  list of register dicts
* RegisterDB                      : thin, thread-safe sqlite wrapper

Markdown format (one register per row, extra text/headings are ignored):

| Address | Kind    | Name            | Value | Writable | Scale | Unit |
|---------|---------|-----------------|-------|----------|-------|------|
| 100     | input   | Temperature     | 215   | no       | 0.1   | C    |
| 200     | holding | Setpoint        | 0     | yes      |       |      |

Value is the RAW 16-bit register value (decimal or 0x hex).
Scale/Unit are informational only (e.g. scale 0.1 => raw 2530 means 253.0).
Kind defaults to 'holding' when left blank.
"""
import logging
import re
import sqlite3
import threading
from pathlib import Path

log = logging.getLogger("regdb")

HEADER = ["Address", "Kind", "Name", "Value", "Writable", "Scale", "Unit"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS registers (
    address       INTEGER PRIMARY KEY,
    kind          TEXT    NOT NULL DEFAULT 'holding',
    name          TEXT,
    value         INTEGER NOT NULL DEFAULT 0,
    default_value INTEGER NOT NULL DEFAULT 0,
    writable      INTEGER NOT NULL DEFAULT 0,
    scale         REAL,
    unit          TEXT,
    updated_at    TEXT    DEFAULT CURRENT_TIMESTAMP
)
"""

_ADDR_RE = re.compile(r"0x[0-9a-fA-F]+|\d+")


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------
def parse_markdown(path):
    rows, seen = [], set()
    text = Path(path).read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not _ADDR_RE.fullmatch(cells[0]):
            continue  # header or separator row
        if len(cells) < 5:
            raise ValueError(f"{path}:{lineno}: expected at least 5 columns")
        cells += [""] * (7 - len(cells))

        addr = int(cells[0], 0)
        value = int(cells[3], 0)
        if not 0 <= addr <= 0xFFFF:
            raise ValueError(f"{path}:{lineno}: address {addr} out of range")
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"{path}:{lineno}: value {value} is not a 16-bit unsigned number")
        if addr in seen:
            raise ValueError(f"{path}:{lineno}: duplicate address {addr}")
        seen.add(addr)

        rows.append({
            "address": addr,
            "kind": cells[1].lower() or "holding",
            "name": cells[2],
            "value": value,
            "writable": cells[4].lower() in ("yes", "y", "true", "1"),
            "scale": float(cells[5]) if cells[5] else None,
            "unit": cells[6],
        })
    return rows


def write_markdown(path, rows, title="Register defaults", note=""):
    lines = [f"# {title}", ""]
    if note:
        lines += [note, ""]
    lines += ["| " + " | ".join(HEADER) + " |",
              "|" + "|".join("---" for _ in HEADER) + "|"]
    for r in sorted(rows, key=lambda r: r["address"]):
        scale = "" if r.get("scale") in (None, "") else f"{r['scale']:g}"
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            r["address"], r["kind"], r["name"].replace("|", "/"), r["value"],
            "yes" if r["writable"] else "no", scale, r.get("unit", "")))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# SQLite
# --------------------------------------------------------------------------
class RegisterDB:
    def __init__(self, path):
        self.path = str(path)
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        with self.lock:
            self.conn.execute(SCHEMA)
            self.conn.commit()

    def count(self):
        with self.lock:
            return self.conn.execute("SELECT COUNT(*) FROM registers").fetchone()[0]

    def load_defaults(self, rows, keep_values=False):
        """Load markdown rows. keep_values=True preserves current values of
        registers that already exist (metadata + defaults are still refreshed)."""
        with self.lock:
            if not keep_values:
                self.conn.execute("DELETE FROM registers")
            self.conn.executemany(
                """INSERT INTO registers
                       (address, kind, name, value, default_value, writable, scale, unit)
                   VALUES (:address, :kind, :name, :value, :value, :writable, :scale, :unit)
                   ON CONFLICT(address) DO UPDATE SET
                       kind=excluded.kind, name=excluded.name,
                       default_value=excluded.default_value,
                       writable=excluded.writable, scale=excluded.scale,
                       unit=excluded.unit""",
                [{**r, "writable": int(r["writable"])} for r in rows])
            self.conn.commit()

    def read(self, address, count):
        """Return `count` values starting at `address` (missing => 0)."""
        end = address + count - 1
        with self.lock:
            cur = self.conn.execute(
                "SELECT address, value FROM registers WHERE address BETWEEN ? AND ?",
                (address, end))
            found = dict(cur.fetchall())
        return [found.get(a, 0) for a in range(address, end + 1)]

    def all_exist(self, address, count):
        end = address + count - 1
        with self.lock:
            n = self.conn.execute(
                "SELECT COUNT(*) FROM registers WHERE address BETWEEN ? AND ?",
                (address, end)).fetchone()[0]
        return n == count

    def write(self, address, values, allow_readonly=False, create_unknown=True):
        """Update register values. Read-only registers are ignored (logged)."""
        with self.lock:
            for i, val in enumerate(values):
                addr = address + i
                val &= 0xFFFF
                row = self.conn.execute(
                    "SELECT writable, name FROM registers WHERE address=?", (addr,)).fetchone()
                if row is None:
                    if not create_unknown:
                        log.warning("write to unknown register %d ignored", addr)
                        continue
                    self.conn.execute(
                        "INSERT INTO registers (address, kind, value, default_value, writable) "
                        "VALUES (?, ?, ?, 0, 1)",
                        (addr, "holding", val))
                    log.info("WRITE %d (new) = %d", addr, val)
                    continue
                writable, name = row
                if not writable and not allow_readonly:
                    log.warning("write to read-only register %d (%s) ignored", addr, name)
                    continue
                self.conn.execute(
                    "UPDATE registers SET value=?, updated_at=CURRENT_TIMESTAMP WHERE address=?",
                    (val, addr))
                log.info("WRITE %d (%s) = %d", addr, name, val)
            self.conn.commit()
