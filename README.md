# Dummy Modbus TCP server

A Modbus TCP server that behaves like the device you describe, for developing and testing clients without touching real hardware. It is not tied to any manufacturer: a device is just a register spec file in `specs/` (Solis is bundled as one example).

- Register defaults live in a **markdown file** (`defaults.md`).
- On start-up they are loaded into an **sqlite database**; the server answers every read and applies every write against that database, so values persist between runs.
- A **dump script** reads a real device and generates the markdown file. *What* it reads is described by a YAML spec from `specs/` (e.g. `specs/solis.yml`), not hardcoded.

```
 real device ──(dump_defaults.py + specs/<device>.yml)──▶ defaults.md ──(init_db.py)──▶ server.db ◀──▶ server.py ◀── Modbus client
```

## Files

| File | Purpose |
|---|---|
| `server.py` | Modbus TCP server backed by sqlite |
| `init_db.py` | Loads `defaults.md` into `server.db` |
| `dump_defaults.py` | Reads a real device and writes a defaults markdown file (read-only) |
| `defaults.md` | Default register values (a small hand-made demonstration set is included) |
| `spec.py` | Loader/expander for spec files |
| `regdb.py` | Shared markdown parsing and sqlite access |
| `specs/*.yml` | Register specifications used by the dump script, one per device (addresses, names, scale, unit, input/holding). Bundled: `solis.yml` |

## Install

Python 3.10+.

```bash
pip install -r requirements.txt
```

## Quick start

```bash
python init_db.py                   # defaults.md -> server.db
sudo python server.py               # listens on 0.0.0.0:502
# no root?   python server.py --port 1502
```

`server.py` also creates the database from `defaults.md` automatically if `server.db` does not exist, so `init_db.py` is only needed to reset or to load a different file.

## How requests are handled

| Modbus request | Behaviour |
|---|---|
| FC03 read holding / FC04 read input | Values are read from the matching rows. Registers not in the DB read as `0`. |
| FC06 write single / FC16 write multiple | The matching rows are updated. Registers marked `Writable = no` are ignored and logged. |

For simplicity input and holding registers share one address space, so a spec must not use the same address for both kinds.

### Server options

| Option | Meaning |
|---|---|
| `--host`, `--port` | Bind address (default `0.0.0.0:502`) |
| `--db` | sqlite file (default `server.db`) |
| `--md` | Defaults file used for first-run init and `--reset` (default `defaults.md`) |
| `--reset` | Reload defaults from markdown before starting (discards current values) |
| `--strict` | Unknown registers return a Modbus illegal-address error instead of `0`, and writes to them are rejected |
| `--allow-readonly-writes` | Let clients overwrite registers marked `Writable = no` |
| `-v` | Also log every read |

## Defaults file format

Any markdown table row whose first cell is a number is a register; headings and prose are ignored.

```markdown
| Address | Kind    | Name          | Value | Writable | Scale | Unit |
|---------|---------|---------------|-------|----------|-------|------|
| 100     | input   | Temperature   | 215   | no       | 0.1   | C    |
| 200     | holding | Setpoint      | 0     | yes      |       |      |
```

- **Value** is the raw unsigned 16-bit register value, decimal or `0x` hex. A value of `2530` for a register with scale `0.1` means 253.0.
- **Kind** is `input` or `holding`; a blank cell means `holding`.
- **Scale** and **Unit** are informational only; the server never applies them.
- 32-bit quantities occupy two rows (high word first).
- Duplicate addresses and out-of-range values are rejected with the line number.

## Generating defaults from a real device

`dump_defaults.py` only issues read requests (FC03/FC04); it never writes to the device. The register list comes from a spec, which you must choose with `--spec`: either a name from `specs/` (`solis` finds `specs/solis.yml` or `specs/solis.yaml`) or a path to any YAML file.

```bash
python dump_defaults.py 192.168.1.100 --spec solis                 # -> defaults.md
python dump_defaults.py 192.168.1.100 --spec ./my_device.yaml -o my.md
python dump_defaults.py 192.168.1.100 --spec solis --extra holding:100-200
python init_db.py --md my.md                                       # load the result
```

Registers the device refuses (not supported by that model or firmware) are skipped and listed at the end. If the Wi-Fi/LAN dongle drops requests, raise `--delay` or lower `--block`. Command-line options override the corresponding values in the spec.

Registers marked `holding` in the spec are written as `Writable = yes`, `input` ones as `no`; edit the generated markdown to change this.

## Register specs (`specs/`)

The dump script contains no device knowledge. A spec file describes one device, so you can add `specs/other_device.yml` (or `.yaml`) without touching any code. The register list is flat: if a spec covers several models, registers a particular device does not have are simply skipped by the dump.

```yaml
device: {name: Example meter}
connection: {port: 502, device_id: 1}
reading:    {block: 10, delay: 0.05, timeout: 3}

groups:
  - name: measurements            # group names are only labels
    kind: input                   # input = FC04, holding = FC03
    registers:
      - {address: 100, name: Temperature, scale: 0.1, unit: C}
      - {address: 102, name: Total Energy, width: 2, scale: 1, unit: kWh}   # 32-bit: 2 rows
      - {address: 110, name: "Voltage {n}", repeat: 3, stride: 2, scale: 0.1, unit: V}
      - {address: 120, name: "{i} Phase Current", repeat: [A, B, C], scale: 0.01, unit: A}
      - address: 200              # consecutive registers
        names: [Model, Firmware, Status]
```

| Field | Meaning |
|---|---|
| `address` | First register (decimal). Required. |
| `name` / `names` | One name, or a list of consecutive registers. List items can be strings or mappings (`name`, `scale`, `unit`, `width`, `writable`). |
| `kind` | `input` or `holding`; usually set once on the group. |
| `width` | `1` (default) or `2` for a 32-bit value. Two rows are generated, suffixed ` (high word)` / ` (low word)`. |
| `scale`, `unit` | Informational; copied into the markdown. |
| `writable` | Overrides the default (`holding` → yes, `input` → no, see `defaults:` in the spec). |
| `repeat`, `stride` | Repeat the entry or block `N` times (or once per list item). `stride` is the distance between repeats; it defaults to the block size. In names, `{n}` is the 1-based counter and `{i}` the list item. |

Spec mistakes (bad kind, bad name template, unknown spec name, …) stop the script with a message naming the group and entry. If two entries define the same address, a warning is logged and the later one wins.

The bundled `solis.yml` covers the Ginlong Solis hybrid-inverter and string-inverter registers used so far (555 registers); extend it from the Solis Modbus documentation as needed.

## Notes

- Values are static until a client writes them; there is no simulation of PV or battery behaviour.
- The server has no authentication; run it on a trusted network.
- Port 502 is privileged on Linux. Use `--port 1502` (and a client that supports a custom port) if you do not want to run as root.
