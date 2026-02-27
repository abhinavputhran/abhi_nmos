#!/usr/bin/env python3
"""Single entry point: extract (all files) or plot (one file) or plot-all (all files)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_all.py extract | plot <file.xls> | plot-all")
        print("  extract   -> nmos_summary.csv + per-Vg CSV (use --dir to point at data)")
        print("  plot      -> all 6 plots for one file")
        print("  plot-all  -> all plots for all .xls in --dir")
        return 0
    cmd = sys.argv[1].lower()
    if cmd == "extract":
        from run_extract_all import main as extract_main
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return extract_main()
    if cmd == "plot":
        if len(sys.argv) < 3:
            print("Usage: python run_all.py plot <path_to.xls> [--out-dir DIR]")
            return 1
        from plot_xls import plot_file
        path = sys.argv[2]
        out_dir = None
        for i, a in enumerate(sys.argv[3:], 3):
            if a == "--out-dir" and i + 1 < len(sys.argv):
                out_dir = sys.argv[i + 1]
                break
        return plot_file(path, out_dir=out_dir)
    if cmd == "plot-all":
        from plot_all_xls import main as plot_all_main
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return plot_all_main()
    print("Unknown command. Use: extract | plot | plot-all")
    return 1


if __name__ == "__main__":
    sys.exit(main())
