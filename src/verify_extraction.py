#!/usr/bin/env python3
"""Print raw data and computed metrics for one file — useful to double-check the math."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nmos_utils import (
    load_xls_data,
    get_sweep_grid,
    extract_vth_max_gm_extrapolation,
    compute_metrics_at_vd,
    parse_filename,
)

VD_REF = 5.0


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_extraction.py <file.xls>")
        return 1
    path = sys.argv[1]
    if not Path(path).is_file():
        print(f"File not found: {path}")
        return 1

    info = parse_filename(path)
    print("=" * 60)
    print("FILE:", path)
    if info:
        print("  chip:", info["chip"], "  fet_size:", info["fet_size"])
    print("=" * 60)

    df = load_xls_data(path)
    if df.empty:
        print("No data.")
        return 1

    mask = (df["DrainV"] >= VD_REF - 0.02) & (df["DrainV"] <= VD_REF + 0.02)
    sub = df.loc[mask].groupby("GateV", sort=True).agg({"DrainI": "mean", "GateI": "mean"}).reset_index().sort_values("GateV")

    print("\n1. RAW DATA at Vd =", VD_REF, "V")
    print("-" * 50)
    print(f"{'GateV (V)':<12} {'DrainI (A)':<18} {'DrainI (uA)':<14} {'GateI (A)':<14}")
    for _, row in sub.iterrows():
        gv, di, gi = row["GateV"], row["DrainI"], row["GateI"]
        print(f"{gv:<12.1f} {di:<18.6e} {di*1e6:<14.2f} {gi:<14.4e}")

    print("\n2. Vth (max-gm extrapolation)")
    for vd in (0.2, 1.0, 5.0, 10.0):
        vth, vg0, id0, gm_max, ok = extract_vth_max_gm_extrapolation(df, vd_ref=vd)
        if ok:
            print(f"   Vd = {vd} V:  Vth = {vg0:.4f} - {id0:.2e}/{gm_max:.2e} = {vth:.4f} V  (max gm at Vg={vg0:.3f}, Id={id0*1e6:.2f} uA)")
        else:
            print(f"   Vd = {vd} V:  (failed)")

    print("\n3. ON/OFF at Vd =", VD_REF, "V")
    m = compute_metrics_at_vd(df, vd_ref=VD_REF)
    vd_actual = m["Vd_ref"]
    print("   Ion  =", m["Ion"], "A   Ioff =", m["Ioff"], "A")
    print("   Ron  =", vd_actual, "/|Ion|  =", m["Ron"], "ohm")
    print("   Roff =", vd_actual, "/|Ioff| =", m["Roff"], "ohm   ratio =", m["Ion_Ioff_ratio"])

    print("\n4. Sanity: Ion/Ioff should match table above at Vg=", m["vg_on"], "/", m["vg_off"])
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
