#!/usr/bin/env python3
"""Batch extract metrics from all nmos* pattern* chip*.xls files. Writes summary + per-Vg CSVs."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from nmos_utils import collect_all_xls, extract_all_metrics


def main():
    p = argparse.ArgumentParser(description="Extract NMOS metrics from all XLS files")
    p.add_argument("--dir", default=".", help="Directory containing .xls files")
    p.add_argument("--out", default="nmos_summary.csv", help="Output summary CSV")
    p.add_argument("--out-per-vg", default="nmos_summary_per_gate_voltage.csv", help="Per-Vg CSV")
    p.add_argument("--excel", action="store_true", help="Also write .xlsx")
    p.add_argument("--vd-ref", type=float, default=5.0, help="Vd for Ion/Ioff (V)")
    p.add_argument("--vg-off", type=float, default=0.0, help="Vg for off state (V)")
    args = p.parse_args()

    dirpath = Path(args.dir)
    files = collect_all_xls(dirpath)
    if not files:
        print("No nmos* pattern* chip*.xls files in", dirpath.resolve(), file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(files)} files ...")
    rows_summary, rows_per_vg = [], []

    for f in files:
        res = extract_all_metrics(str(f), vd_ref=args.vd_ref, vg_off=args.vg_off)
        if res is None:
            continue
        m = res.get("metrics")
        rows_summary.append({
            "chip": res["chip"], "nmos": res["nmos"], "pattern": res["pattern"],
            "fet_size": res["fet_size"], "filename": res["filename"],
            "Vth_Vd1V": res.get("Vth_Vd1V"), "Vth_Vd5V": res.get("Vth_Vd5V"),
            "Vth_Vd10V": res.get("Vth_Vd10V"), "Vth_Vd200mV": res.get("Vth_Vd200mV"),
            "Vd_ref_V": m["Vd_ref"] if m else None, "Ion_A": m["Ion"] if m else None,
            "Ioff_A": m["Ioff"] if m else None, "Ron_ohm": m["Ron"] if m else None,
            "Roff_ohm": m["Roff"] if m else None, "Ion_Ioff_ratio": m["Ion_Ioff_ratio"] if m else None,
        })
        if m:
            for i, gv in enumerate(m["GateV"]):
                rows_per_vg.append({
                    "chip": res["chip"], "fet_size": res["fet_size"], "GateV_V": gv,
                    "DrainI_at_Vd_A": m["DrainI_at_Vd"][i], "R_at_Vd_ohm": m["R_at_Vd"][i],
                    "GateI_at_Vd_A": m["GateI_at_Vd"][i],
                })

    df_summary = pd.DataFrame(rows_summary).sort_values(["chip", "nmos", "pattern"])
    df_per_vg = pd.DataFrame(rows_per_vg).sort_values(["chip", "fet_size", "GateV_V"])
    out_path = dirpath / args.out
    out_per_vg_path = dirpath / args.out_per_vg
    df_summary.to_csv(out_path, index=False)
    df_per_vg.to_csv(out_per_vg_path, index=False)
    print(f"Wrote {out_path} ({len(df_summary)} devices)")
    print(f"Wrote {out_per_vg_path} ({len(df_per_vg)} rows)")
    if args.excel:
        with pd.ExcelWriter(dirpath / "nmos_summary.xlsx", engine="openpyxl") as w:
            df_summary.to_excel(w, sheet_name="Summary", index=False)
            df_per_vg.to_excel(w, sheet_name="Per_GateV", index=False)
        print("Wrote nmos_summary.xlsx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
