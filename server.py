#!/usr/bin/env python3
"""Dummy Modbus Server - Modbus TCP server backed by sqlite.

Every read (FC03 holding / FC04 input) is answered from the `registers` table,
every write (FC06 / FC16) updates the matching row.  Both register types share
one address space.

    python server.py                 # 0.0.0.0:502  (port 502 needs root on Linux)
    python server.py --port 1502
    python server.py --reset         # reload defaults.md before starting
"""
import argparse
import asyncio
import logging
import os
import sys

from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext
from pymodbus.datastore.store import BaseModbusDataBlock
from pymodbus.server import StartAsyncTcpServer

from regdb import RegisterDB, parse_markdown

log = logging.getLogger("dummy-modbus-server")


class SqliteDataBlock(BaseModbusDataBlock):
    """Datablock that has no memory of its own - everything lives in sqlite."""

    def __init__(self, db, strict=False, allow_readonly=False):
        self.db = db
        self.strict = strict
        self.allow_readonly = allow_readonly

    def reset(self):
        pass

    def validate(self, address, count=1):
        # strict: unknown registers -> Modbus "illegal data address" exception
        # lenient: unknown registers read as 0 and writes create new rows
        return self.db.all_exist(address, count) if self.strict else True

    def getValues(self, address, count=1):
        values = self.db.read(address, count)
        log.debug("READ  %d x%d -> %s", address, count, values)
        return values

    def setValues(self, address, values):
        if isinstance(values, int):
            values = [values]
        self.db.write(address, list(values),
                      allow_readonly=self.allow_readonly,
                      create_unknown=not self.strict)


def build_context(db, strict, allow_readonly):
    block = SqliteDataBlock(db, strict, allow_readonly)
    # zero_mode=True: request address N maps to register N (no +1 offset)
    device = ModbusDeviceContext(di=block, co=block, hr=block, ir=block, zero_mode=True)
    return ModbusServerContext(devices=device, single=True)


def main():
    ap = argparse.ArgumentParser(description="Dummy Modbus TCP server")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=502)
    ap.add_argument("--db", default="server.db")
    ap.add_argument("--md", default="defaults.md", help="defaults file used for auto-init / --reset")
    ap.add_argument("--reset", action="store_true", help="reload defaults from markdown before starting")
    ap.add_argument("--strict", action="store_true",
                    help="reads/writes of registers not in the DB raise an illegal-address error")
    ap.add_argument("--allow-readonly-writes", action="store_true",
                    help="let clients overwrite registers marked Writable=no")
    ap.add_argument("-v", "--verbose", action="store_true", help="log every read as well")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s")
    logging.getLogger("pymodbus").setLevel(logging.WARNING)

    first_run = not os.path.exists(args.db)
    db = RegisterDB(args.db)
    if first_run or args.reset or db.count() == 0:
        try:
            rows = parse_markdown(args.md)
        except (OSError, ValueError) as e:
            sys.exit(f"[-] Cannot load defaults: {e}")
        db.load_defaults(rows)
        log.info("Loaded %d default registers from %s", len(rows), args.md)

    context = build_context(db, args.strict, args.allow_readonly_writes)
    log.info("Dummy Modbus TCP server listening on %s:%d (db=%s, %d registers)",
             args.host, args.port, args.db, db.count())
    try:
        asyncio.run(StartAsyncTcpServer(context=context, address=(args.host, args.port)))
    except KeyboardInterrupt:
        log.info("Stopped")
    except PermissionError:
        sys.exit(f"[-] No permission to bind port {args.port} - use --port 1502 or run as root")


if __name__ == "__main__":
    main()
