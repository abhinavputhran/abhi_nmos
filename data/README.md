# Data

Drop your probe `.xls` files here.

Expected naming: `nmos{N} pattern{M} chip{C}.xls` (e.g. `nmos1 pattern2 chip19.xls`). The scripts look for that pattern and will process all matching files in this directory.

When you run extraction or plotting, point the scripts at this folder with `--dir data` (from the repo root).
