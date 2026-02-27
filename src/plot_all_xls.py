#!/usr/bin/env python3
"""Plot all graphs for every nmos* pattern* chip*.xls in a directory."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nmos_utils import collect_all_xls
from plot_xls import plot_file


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default=".", help="Directory with .xls files")
    p.add_argument("--out-dir", default=None, help="Where to save plots (default: next to each file)")
    p.add_argument("--dpi", type=int, default=150)
    args = p.parse_args()

    dirpath = Path(args.dir)
    files = collect_all_xls(dirpath)
    if not files:
        print("No nmos* pattern* chip*.xls in", dirpath.resolve(), file=sys.stderr)
        return 1

    print(f"Plotting {len(files)} files ...")
    failed = 0
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name}")
        if plot_file(str(f), out_dir=args.out_dir, dpi=args.dpi) != 0:
            failed += 1
    print(f"Done. {len(files) - failed} ok." + (f" ({failed} failed)" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
