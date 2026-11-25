"""Loader for register specification files (see specs/).

Turns the compact YAML description (groups, repeats, 32-bit widths) into a flat
{address: RegisterSpec} map.  Contains no device knowledge and no Modbus code.
"""
import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

log = logging.getLogger("spec")

SPECS_DIR = Path(__file__).resolve().parent / "specs"

KINDS = ("input", "holding")

DEFAULT_SETTINGS = {
    "connection": {"port": 502, "device_id": 1},
    "reading": {"block": 10, "delay": 0.05, "timeout": 3},
    "defaults": {
        "writable": {"input": False, "holding": True},
        "word_names": [" (high word)", " (low word)"],
    },
}


class SpecError(ValueError):
    pass


@dataclass(frozen=True)
class RegisterSpec:
    address: int
    kind: str
    name: str
    scale: float | None
    unit: str
    writable: bool


class Spec:
    def __init__(self, data, path="<spec>"):
        self.path = path
        self.data = data
        self.device_name = (data.get("device") or {}).get("name", "device")
        self.connection = {**DEFAULT_SETTINGS["connection"], **(data.get("connection") or {})}
        self.reading = {**DEFAULT_SETTINGS["reading"], **(data.get("reading") or {})}
        self.defaults = {**DEFAULT_SETTINGS["defaults"], **(data.get("defaults") or {})}
        self.groups = data.get("groups")
        if not isinstance(self.groups, list) or not self.groups:
            raise SpecError(f"{path}: 'groups' must be a non-empty list")

    def expand(self):
        """Return {address: RegisterSpec} for every register in the spec."""
        regs = {}
        for g in self.groups:
            gname = g.get("name", "<unnamed group>")
            kind = g.get("kind")
            entries = g.get("registers")
            if not isinstance(entries, list):
                raise SpecError(f"group '{gname}': 'registers' must be a list")
            for e in entries:
                for r in self._expand_entry(e, kind, gname):
                    if r.address in regs:
                        log.warning("address %d defined twice (%r overrides %r)",
                                    r.address, r.name, regs[r.address].name)
                    regs[r.address] = r
        return regs

    def _expand_entry(self, e, group_kind, gname):
        ctx = f"group '{gname}', entry {e!r}"
        if not isinstance(e, dict) or "address" not in e:
            raise SpecError(f"{ctx}: entry needs an 'address'")
        if ("name" in e) == ("names" in e):
            raise SpecError(f"{ctx}: give exactly one of 'name' or 'names'")
        kind = e.get("kind", group_kind)
        if kind not in KINDS:
            raise SpecError(f"{ctx}: kind must be one of {KINDS}, got {kind!r}")

        base = {"scale": e.get("scale"), "unit": e.get("unit", ""),
                "width": e.get("width", 1), "writable": e.get("writable")}
        items = e["names"] if "names" in e else [e["name"]]
        if not isinstance(items, list) or not items:
            raise SpecError(f"{ctx}: 'names' must be a non-empty list")

        # one block = the consecutive registers described by `items`
        block, offset = [], 0
        for it in items:
            m = {"name": it} if isinstance(it, str) else dict(it)
            if "name" not in m:
                raise SpecError(f"{ctx}: list item without a name: {it!r}")
            for k, v in base.items():
                m.setdefault(k, v)
            if m["width"] not in (1, 2):
                raise SpecError(f"{ctx}: width must be 1 or 2")
            block.append((offset, m))
            offset += m["width"]
        block_size = offset

        rep = e.get("repeat", 1)
        if isinstance(rep, int):
            if rep < 1:
                raise SpecError(f"{ctx}: repeat must be >= 1")
            repeats = [(n, n) for n in range(1, rep + 1)]          # ({n}, {i})
        elif isinstance(rep, list) and rep:
            repeats = [(n, item) for n, item in enumerate(rep, 1)]
        else:
            raise SpecError(f"{ctx}: repeat must be an int or a non-empty list")
        stride = e.get("stride", block_size)

        try:
            start = int(e["address"])
        except (TypeError, ValueError):
            raise SpecError(f"{ctx}: address must be an integer")

        for k, (n, item) in enumerate(repeats):
            for off, m in block:
                try:
                    name = str(m["name"]).format(n=n, i=item)
                except (KeyError, IndexError, ValueError) as ex:
                    raise SpecError(f"{ctx}: bad name template {m['name']!r}: {ex}")
                addr = start + k * stride + off
                yield from self._words(addr, kind, name, m)

    def _words(self, addr, kind, name, m):
        writable = m["writable"]
        if writable is None:
            writable = bool(self.defaults["writable"][kind])
        scale = None if m["scale"] is None else float(m["scale"])
        if m["width"] == 1:
            yield RegisterSpec(addr, kind, name, scale, m["unit"], writable)
        else:
            hi, lo = self.defaults["word_names"]
            yield RegisterSpec(addr, kind, name + hi, scale, m["unit"], writable)
            yield RegisterSpec(addr + 1, kind, name + lo, scale, m["unit"], writable)


def resolve_spec(name):
    """Turn a --spec argument into a file path.

    Accepts an explicit path (any extension) or a bare device name such as
    'solis', which is looked up as specs/solis.yml or specs/solis.yaml.
    """
    p = Path(name)
    if p.is_file():
        return p
    if p.parent == Path(".") and p.suffix == "":
        for ext in (".yml", ".yaml"):
            cand = SPECS_DIR / (p.name + ext)
            if cand.is_file():
                return cand
    available = sorted(f.stem for f in SPECS_DIR.glob("*.y*ml")) if SPECS_DIR.is_dir() else []
    hint = f" (known specs: {', '.join(available)})" if available else ""
    raise SpecError(f"spec '{name}' not found{hint}")


def load_spec(path):
    path = resolve_spec(path)
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except OSError as e:
        raise SpecError(f"cannot read spec file: {e}")
    except yaml.YAMLError as e:
        raise SpecError(f"{path}: invalid YAML: {e}")
    if not isinstance(data, dict):
        raise SpecError(f"{path}: top level must be a mapping")
    return Spec(data, path)
