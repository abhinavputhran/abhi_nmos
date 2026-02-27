#!/usr/bin/env python3
"""Plot Id vs Vg (Vth), GateI vs Vd, and Id vs Vd for one XLS file."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from nmos_utils import load_xls_data, get_sweep_grid, get_id_vs_vg_at_vd, extract_vth_max_gm_extrapolation, parse_filename


def plot_file(filepath, out_dir=None, dpi=150):
    filepath = Path(filepath)
    if not filepath.is_file():
        print(f"File not found: {filepath}", file=sys.stderr)
        return 1
    info = parse_filename(filepath)
    label = info["fet_size"] + f" chip{info['chip']}" if info else filepath.stem
    df = load_xls_data(str(filepath))
    if df.empty:
        print("No data.", file=sys.stderr)
        return 1

    drain_v, gate_v = get_sweep_grid(df)
    gate_v_unique = np.sort(np.unique(gate_v))
    out_dir = Path(out_dir or filepath.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / filepath.stem.replace(" ", "_")

    vd_configs = [(0.2, "200mV"), (1.0, "1V"), (10.0, "10V"), (5.0, "5V")]
    for vd_plot, vd_label in vd_configs:
        vgs, ids = get_id_vs_vg_at_vd(df, vd_ref=vd_plot)
        vgs, ids = np.asarray(vgs), np.asarray(ids)
        vth, vg0, id0, gm_max, success = extract_vth_max_gm_extrapolation(df, vd_ref=vd_plot)
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(vgs, ids * 1e6, "b.-", markersize=6, label=f"$I_d$ at $V_d$={vd_plot} V")
        if success:
            vg_tan = np.array([min(vgs.min(), vth) - 0.2, vgs.max() + 0.2])
            id_tan = (id0 + gm_max * (vg_tan - vg0)) * 1e6
            ax.plot(vg_tan, id_tan, "r--", linewidth=2, label="Tangent at max $g_m$")
            ax.axvline(x=vth, color="green", linestyle=":", linewidth=2, label=f"$V_{{th}}$ = {vth:.3f} V")
            ax.axhline(y=0, color="gray", linestyle="-", linewidth=0.5)
            ax.plot(vg0, id0 * 1e6, "ro", markersize=8, label="Max $g_m$ point")
        ax.set_xlabel("Gate voltage $V_g$ (V)")
        ax.set_ylabel("Drain current $I_d$ (µA)")
        ax.set_title(f"$I_d$ vs $V_g$ at $V_d$={vd_plot} V — {label}\n(max-$g_m$ linear extrapolation)")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)
        ax.set_xlim(left=min(0, vgs.min()))
        ax.set_ylim(bottom=0)
        fig.tight_layout()
        fig.savefig(f"{base}_DrainI_vs_GateV_Vd{vd_label}_Vth.png", dpi=dpi)
        plt.close(fig)
        print(f"Saved {base}_DrainI_vs_GateV_Vd{vd_label}_Vth.png (Vth = {vth:.4f} V)" if success else f"Saved ... Vd{vd_label}_Vth.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    for gv in gate_v_unique:
        mask = df["GateV"] == gv
        dv = df.loc[mask, "DrainV"].values
        gi = df.loc[mask, "GateI"].values
        ax.plot(dv[np.argsort(dv)], np.array(gi)[np.argsort(dv)] * 1e9, label=f"Vg={gv:.0f} V", marker=".", markersize=2)
    ax.set_xlabel("Drain voltage $V_d$ (V)")
    ax.set_ylabel("Gate current $I_g$ (nA)")
    ax.set_title(f"Gate current vs drain voltage — {label}")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    fig.tight_layout()
    fig.savefig(f"{base}_GateI_vs_DrainV.png", dpi=dpi)
    plt.close(fig)
    print(f"Saved {base}_GateI_vs_DrainV.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    for gv in gate_v_unique:
        mask = df["GateV"] == gv
        dv = df.loc[mask, "DrainV"].values
        di = df.loc[mask, "DrainI"].values
        o = np.argsort(dv)
        ax.plot(dv[o], np.array(di)[o] * 1e6, label=f"Vg={gv:.0f} V", marker=".", markersize=2)
    ax.set_xlabel("Drain voltage $V_d$ (V)")
    ax.set_ylabel("Drain current $I_d$ (µA)")
    ax.set_title(f"Drain current vs drain voltage — {label}")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    fig.tight_layout()
    fig.savefig(f"{base}_DrainI_vs_DrainV.png", dpi=dpi)
    plt.close(fig)
    print(f"Saved {base}_DrainI_vs_DrainV.png")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("xls_file")
    p.add_argument("--out-dir", default=None)
    p.add_argument("--dpi", type=int, default=150)
    args = p.parse_args()
    return plot_file(args.xls_file, out_dir=args.out_dir, dpi=args.dpi)


if __name__ == "__main__":
    sys.exit(main())
