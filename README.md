# NMOS probe data

Scripts to process IV data from NMOS transistor probing. I had 94 `.xls` files (naming: `nmos{N} pattern{M} chip{19|50}.xls`) and wanted threshold voltage, on/off current and resistance, and plots — all keyed by chip and FET size.

## Repo layout

```
abhi_nmos/
├── data/                       # put your .xls files here
├── src/                        # all Python scripts
├── docs/                       # calculation notes (how Vth, Ion, Roff, etc. are derived)
├── graphs/                     # processed data graphs
├── keithley generated graphs/ 
├── requirements.txt
└── README.md
```

## Setup

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Quick start

1. Put your probe `.xls` files in `data/` (or leave them in the repo root and use `--dir .` below).
2. Run from the **repo root** so paths work:

**Extract metrics for all files** (writes CSVs into the same dir as the data):

```bash
python src/run_all.py extract --dir data
```

Output: `data/nmos_summary.csv` (one row per device: Vth at 200mV/1V/5V/10V, Ion, Ioff, Ron, Roff, ratio) and `data/nmos_summary_per_gate_voltage.csv` (per-Vg breakdown). Add `--excel` to get `nmos_summary.xlsx` too.

**Plot one file** (6 PNGs: Id vs Vg at 4 Vds for Vth, then GateI vs Vd, then Id vs Vd):

```bash
python src/plot_xls.py "data/nmos1 pattern2 chip19.xls"
```

Plots are saved next to the file by default. Use `--out-dir ./plots` to send them somewhere else.

**Plot all 94 files:**

```bash
python src/run_all.py plot-all --dir data
```

**Where plots are saved**

- **Single file:** The 6 PNGs go in the **same folder as the .xls file** (e.g. file in `data/` → plots in `data/`). Use `--out-dir <path>` to save elsewhere.
- **Plot-all:** Each file’s 6 plots go **next to that file**. Use `--out-dir <path>` to put all plots in one folder, e.g. `python src/plot_all_xls.py --dir data --out-dir ./all_plots`.

**Check the math on one file:**

```bash
python src/verify_extraction.py "data/nmos1 pattern2 chip19.xls"
```

Prints the raw Id/Ig at Vd=5V and how Vth, Ion, Ioff, Ron, Roff are computed.

## What gets computed

- **Vth** — Linear extrapolation: Id vs Vg at Vd = 200 mV, 1 V, 5 V, 10 V; find max transconductance, draw tangent, extrapolate to Id = 0. The Vg intercept is Vth. Columns: `Vth_Vd200mV`, `Vth_Vd1V`, `Vth_Vd5V`, `Vth_Vd10V`.
- **Ion / Ioff** — Drain current at Vd = 5 V for max Vg (on) and Vg = 0 (off).
- **Ron / Roff** — 5 V / Ion and 5 V / Ioff.
- **Ion_Ioff_ratio** — Ion / Ioff.

Details (which columns we read, which formulas we use) are in `docs/CALCULATIONS.md`.

## Data format

Each `.xls` has a **Data** sheet: columns in groups of four — DrainI(k), DrainV(k), GateI(k), GateV(k) for each curve. We only use those four; chip/nmos/pattern come from the filename.

## License

Use it as you like.
