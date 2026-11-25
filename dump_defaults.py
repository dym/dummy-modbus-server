#!/usr/bin/env python3
"""Read registers from a Modbus TCP device and write them to a defaults markdown file.

Which registers to read (addresses, names, scales, units, input/holding) comes
from a YAML spec file chosen with --spec. This script has no device knowledge
of its own: a spec is a file in specs/ (give its name) or any path.

READ-ONLY: only FC03 (holding) and FC04 (input) reads are issued, nothing is written.

    python dump_defaults.py 192.168.1.100 --spec solis             # specs/solis.yml -> defaults.md
    python dump_defaults.py 192.168.1.100 --spec ./my_device.yaml -o my.md
    python dump_defaults.py 192.168.1.100 --spec solis --extra holding:100-200

Registers the device refuses to return are skipped (a list is printed at the end).
"""
import argparse
import ipaddress
import sys
import time
from pathlib import Path

from regdb import write_markdown
from spec import RegisterSpec, SpecError, load_spec


def parse_extra(text):
    """'holding:100-200' or 'input:0-10'"""
    try:
        kind, rng = text.split(":")
        lo, hi = rng.split("-")
        if kind not in ("holding", "input"):
            raise ValueError
        lo, hi = int(lo), int(hi)
        if not 0 <= lo <= hi <= 0xFFFF:
            raise ValueError
        return kind, lo, hi
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"bad --extra '{text}', expected holding:START-END or input:START-END")


class Reader:
    def __init__(self, ip, port, device_id, timeout, delay):
        from pymodbus.client import ModbusTcpClient
        self.dev, self.delay = device_id, delay
        self.client = ModbusTcpClient(ip, port=port, timeout=timeout)
        if not self.client.connect():
            sys.exit(f"[-] Can't connect to {ip}:{port}")

    def _read(self, kind, addr, count):
        fn = self.client.read_holding_registers if kind == "holding" else self.client.read_input_registers
        try:
            res = fn(address=addr, count=count, device_id=self.dev)
        except Exception:
            self.client.close()
            self.client.connect()
            return None
        finally:
            time.sleep(self.delay)
        if res is None or res.isError():
            return None
        return res.registers

    def read_addresses(self, kind, addresses, block):
        """Return ({addr: value}, [failed addrs]). Tries blocks, falls back to single reads."""
        values, failed = {}, []
        runs, run = [], []
        for a in sorted(addresses):
            if run and (a != run[-1] + 1 or len(run) >= block):
                runs.append(run)
                run = []
            run.append(a)
        if run:
            runs.append(run)

        for run in runs:
            regs = self._read(kind, run[0], len(run)) if len(run) > 1 else None
            if regs is not None and len(regs) == len(run):
                values.update(zip(run, regs))
                continue
            for a in run:  # block failed (or single) -> one by one
                r = self._read(kind, a, 1)
                if r:
                    values[a] = r[0]
                else:
                    failed.append(a)
        return values, failed

    def close(self):
        self.client.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ip", help="IP address of the device")
    ap.add_argument("--spec", required=True,
                    help="register specification: a name from specs/ (e.g. solis) or a path to a YAML file")
    ap.add_argument("-o", "--output", default="defaults.md")
    ap.add_argument("--port", type=int, help="override spec connection.port")
    ap.add_argument("--device-id", type=int, help="override spec connection.device_id")
    ap.add_argument("--block", type=int, help="override spec reading.block (max registers per request)")
    ap.add_argument("--delay", type=float, help="override spec reading.delay (seconds between requests)")
    ap.add_argument("--timeout", type=float, help="override spec reading.timeout (seconds)")
    ap.add_argument("--extra", action="append", type=parse_extra, default=[],
                    metavar="KIND:START-END", help="also read a range that is not in the spec (repeatable)")
    args = ap.parse_args()

    try:
        spec = load_spec(args.spec)
        wanted = spec.expand()
    except SpecError as e:
        sys.exit(f"[-] {e}")

    try:
        ipaddress.ip_address(args.ip)
    except ValueError:
        sys.exit(f"[-] '{args.ip}' is not a valid IP address")

    port = args.port or spec.connection["port"]
    device_id = args.device_id or spec.connection["device_id"]
    block = args.block or spec.reading["block"]
    delay = spec.reading["delay"] if args.delay is None else args.delay
    timeout = args.timeout or spec.reading["timeout"]

    for kind, lo, hi in args.extra:
        for a in range(lo, hi + 1):
            wanted.setdefault(a, RegisterSpec(a, kind, f"reg_{a}", None, "", kind == "holding"))

    rd = Reader(args.ip, port, device_id, timeout, delay)
    print(f"[+] Connected to {args.ip}:{port}, reading {len(wanted)} registers "
          f"(spec {spec.path}, read-only)...")

    by_kind = {"input": [], "holding": []}
    for a, r in wanted.items():
        by_kind[r.kind].append(a)

    rows, failed_all = [], []
    for kind, addrs in by_kind.items():
        if not addrs:
            continue
        print(f"[*] Reading {len(addrs)} {kind} registers...")
        values, failed = rd.read_addresses(kind, addrs, block)
        failed_all += failed
        for a, v in values.items():
            r = wanted[a]
            rows.append(dict(address=a, kind=kind, name=r.name, value=v,
                             writable=r.writable, scale=r.scale, unit=r.unit))
    rd.close()

    if not rows:
        sys.exit("[-] Nothing could be read - check IP, port, device id and that Modbus TCP is enabled")

    note = (f"Generated from {args.ip} on {time.strftime('%Y-%m-%d %H:%M:%S')} using {Path(spec.path).name}. "
            f"{len(rows)} registers read, {len(failed_all)} unavailable. "
            "Value = raw 16-bit register value; Scale/Unit are informational.")
    write_markdown(args.output, rows, title=f"{spec.device_name} register defaults", note=note)
    print(f"[+] Wrote {len(rows)} registers to {args.output}")
    if failed_all:
        print(f"[!] {len(failed_all)} registers not available on this device (skipped): "
              f"{', '.join(map(str, sorted(failed_all)[:30]))}{' ...' if len(failed_all) > 30 else ''}")


if __name__ == "__main__":
    main()
