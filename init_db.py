#!/usr/bin/env python3
"""Load register defaults from a markdown file into the sqlite database.

    python init_db.py                       # defaults.md -> server.db (wipes existing data)
    python init_db.py --keep                # keep current values of existing registers
    python init_db.py --md my.md --db x.db
"""
import argparse
import sys

from regdb import RegisterDB, parse_markdown


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--md", default="defaults.md", help="markdown file with defaults")
    ap.add_argument("--db", default="server.db", help="sqlite database file")
    ap.add_argument("--keep", action="store_true",
                    help="don't overwrite current values of registers already in the DB")
    args = ap.parse_args()

    try:
        rows = parse_markdown(args.md)
    except (OSError, ValueError) as e:
        sys.exit(f"[-] {e}")

    db = RegisterDB(args.db)
    db.load_defaults(rows, keep_values=args.keep)
    print(f"[+] Loaded {len(rows)} registers from {args.md} into {args.db} "
          f"({db.count()} rows total{', values kept' if args.keep else ''})")


if __name__ == "__main__":
    main()
