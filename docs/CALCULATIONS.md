# Data sources, extractions, and calculations

What we read from the XLS, what we only extract (no formula), and what we calculate.

---

## 1. Data from the XLS

Everything comes from the **"Data"** sheet. Row 0 = headers; rows 1+ = sweep points. Columns come in groups of four: `DrainI(k)`, `DrainV(k)`, `GateI(k)`, `GateV(k)` for each curve k. We use DrainV, GateV, DrainI, GateI and reshape into a long table. Chip / nmos / pattern come from the filename (e.g. `nmos3 pattern5 chip50.xls` → chip 50, fet_size = nmos3_pattern5).

---

## 2. Reference point

We don’t interpolate voltage. We pick the sweep row where DrainV is closest to 5 V (or whatever Vd_ref you pass). Same idea for vg_off (0 V) and vg_on (max Vg): we use the GateV in the data that’s closest. So these are just “which row to use,” not extra math.

---

## 3. Vth — max-gm linear extrapolation

Plot Id vs Vg at fixed Vd (we do 200 mV, 1 V, 5 V, 10 V). Find where transconductance gm = dId/dVg is maximum. Draw the tangent at that point and extrapolate to Id = 0; the Vg intercept is Vth.

**Formula:** If the max-gm point is (Vg0, Id0) with slope gm_max, then  
Vth = Vg0 − Id0 / gm_max.

We report Vth_Vd200mV, Vth_Vd1V, Vth_Vd5V, Vth_Vd10V. The 200 mV curve is in the linear region and is usually the one you want for this method.

---

## 4. On/off currents and resistances

**From the data (no formula):** Ion = DrainI at (Vd_ref, vg_on), Ioff = DrainI at (Vd_ref, vg_off). Same for DrainI and GateI per GateV at Vd_ref.

**Calculated:** Ron = Vd_ref / |Ion|, Roff = Vd_ref / |Ioff|, R_at_Vd = Vd_ref / |Id| per Vg, and Ion_Ioff_ratio = |Ion| / |Ioff| (with a small floor to avoid division by zero).
