"""
Utilities for loading NMOS probe data from XLS files and computing FET metrics.
Data is organized by chip and FET size (nmos × pattern).
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd

try:
    import xlrd
    import warnings
    warnings.filterwarnings("ignore", message=".*file size.*")
    warnings.filterwarnings("ignore", message=".*OLE2.*")
except ImportError:
    xlrd = None


def parse_filename(filepath):
    """Parse 'nmos{N} pattern{M} chip{C}.xls' -> dict with nmos, pattern, chip."""
    path = Path(filepath)
    name = path.stem
    m = re.match(r"nmos(\d+)\s+pattern(\d+)\s+chip(\d+)", name, re.IGNORECASE)
    if not m:
        return None
    return {
        "nmos": int(m.group(1)),
        "pattern": int(m.group(2)),
        "chip": int(m.group(3)),
        "fet_size": f"nmos{m.group(1)}_pattern{m.group(2)}",
        "filename": path.name,
    }


def load_xls_data(filepath, sheet_name="Data"):
    """Load the Data sheet from an XLS. Returns DataFrame with DrainV, GateV, DrainI, GateI."""
    if xlrd is None:
        raise ImportError("xlrd is required for .xls files. pip install xlrd")
    wb = xlrd.open_workbook(filepath)
    sheet = wb.sheet_by_name(sheet_name)
    if sheet.nrows < 2:
        return pd.DataFrame()
    headers = sheet.row_values(0)
    n_curves = (len(headers)) // 4
    rows = []
    for r in range(1, sheet.nrows):
        row_vals = sheet.row_values(r)
        for k in range(n_curves):
            i = k * 4
            if i + 3 >= len(row_vals):
                break
            drain_i, drain_v, gate_i, gate_v = row_vals[i], row_vals[i + 1], row_vals[i + 2], row_vals[i + 3]
            if isinstance(drain_i, (int, float)) and isinstance(drain_v, (int, float)):
                rows.append({"DrainV": drain_v, "GateV": gate_v, "DrainI": drain_i, "GateI": gate_i})
    return pd.DataFrame(rows)


def get_sweep_grid(df):
    return np.sort(df["DrainV"].dropna().unique()), np.sort(df["GateV"].dropna().unique())


def get_id_vs_vg_at_vd(df, vd_ref=5.0):
    """(Vg, Id) at fixed Vd, sorted by Vg."""
    drain_v, _ = get_sweep_grid(df)
    vd_actual = drain_v[np.argmin(np.abs(drain_v - vd_ref))] if vd_ref is not None else drain_v[-1]
    mask = (df["DrainV"] >= vd_actual - 0.02) & (df["DrainV"] <= vd_actual + 0.02)
    sub = df.loc[mask].groupby("GateV", sort=True)["DrainI"].mean().reset_index().sort_values("GateV")
    return sub["GateV"].values, sub["DrainI"].values


def extract_vth_max_gm_extrapolation(df, vd_ref=5.0):
    """Vth = Vg0 - Id0/gm_max at point of max transconductance."""
    vgs, ids = get_id_vs_vg_at_vd(df, vd_ref=vd_ref)
    vgs, ids = np.asarray(vgs, dtype=float), np.asarray(ids, dtype=float)
    if len(vgs) < 2:
        return np.nan, np.nan, np.nan, np.nan, False
    gm = np.gradient(ids, vgs)
    idx = np.nanargmax(gm)
    gm_max, vg0, id0 = gm[idx], vgs[idx], ids[idx]
    if gm_max <= 0:
        return np.nan, vg0, id0, gm_max, False
    return float(vg0 - id0 / gm_max), float(vg0), float(id0), float(gm_max), True


def compute_metrics_at_vd(df, vd_ref=5.0, vg_off=0.0, vg_on=None):
    """Ion, Ioff, Ron, Roff, ratio and per-Vg arrays at Vd_ref."""
    drain_v, gate_v = get_sweep_grid(df)
    vd_actual = float(drain_v[np.argmin(np.abs(drain_v - vd_ref))]) if vd_ref is not None else float(drain_v[-1])
    vg_on = float(gate_v.max()) if vg_on is None else vg_on
    mask = (df["DrainV"] >= vd_actual - 0.02) & (df["DrainV"] <= vd_actual + 0.02)
    sub = df.loc[mask].groupby("GateV", sort=True).agg({"DrainI": "mean", "GateI": "mean"}).reset_index().sort_values("GateV")
    gv = sub["GateV"].values
    id_at_vd = sub["DrainI"].values
    ig_at_vd = sub["GateI"].values
    id_safe = np.where(np.abs(id_at_vd) < 1e-20, 1e-20, id_at_vd)
    r_at_vd = vd_actual / np.abs(id_safe)
    idx_off = np.argmin(np.abs(gv - vg_off))
    idx_on = np.argmin(np.abs(gv - vg_on))
    Ioff, Ion = id_at_vd[idx_off], id_at_vd[idx_on]
    Roff = vd_actual / max(np.abs(Ioff), 1e-20)
    Ron = vd_actual / max(np.abs(Ion), 1e-20)
    ratio = np.abs(Ion / max(Ioff, 1e-20)) if Ioff != 0 else np.inf
    return {
        "Vd_ref": vd_actual, "GateV": gv, "DrainI_at_Vd": id_at_vd, "GateI_at_Vd": ig_at_vd,
        "R_at_Vd": r_at_vd, "Ion": Ion, "Ioff": Ioff, "Ron": Ron, "Roff": Roff,
        "Ion_Ioff_ratio": ratio, "vg_off": gv[idx_off], "vg_on": vg_on,
    }


def extract_all_metrics(filepath, vd_ref=5.0, vg_off=0.0, vg_on=None):
    """Load one file, return chip/fet_size, Vth at 200mV/1V/5V/10V, and on/off metrics."""
    info = parse_filename(filepath)
    if info is None:
        return None
    df = load_xls_data(filepath)
    if df.empty:
        return {**info, "Vth_Vd1V": np.nan, "Vth_Vd5V": np.nan, "Vth_Vd10V": np.nan, "Vth_Vd200mV": np.nan, "metrics": None}
    vth_1v, *_ = extract_vth_max_gm_extrapolation(df, vd_ref=1.0)
    vth_5v, *_ = extract_vth_max_gm_extrapolation(df, vd_ref=5.0)
    vth_10v, *_ = extract_vth_max_gm_extrapolation(df, vd_ref=10.0)
    vth_200mv, *_ = extract_vth_max_gm_extrapolation(df, vd_ref=0.2)
    metrics = compute_metrics_at_vd(df, vd_ref=vd_ref, vg_off=vg_off, vg_on=vg_on)
    return {
        **info,
        "Vth_Vd1V": vth_1v, "Vth_Vd5V": vth_5v, "Vth_Vd10V": vth_10v, "Vth_Vd200mV": vth_200mv,
        "metrics": metrics, "df": df,
    }


def collect_all_xls(dirpath="."):
    """All .xls in dirpath matching nmos* pattern* chip*."""
    path = Path(dirpath)
    return sorted(f for f in path.glob("*.xls") if parse_filename(f) is not None)
