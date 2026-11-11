"""Run the whole pipeline in order.

    python pipeline/run_all.py            # steps 1-8, without the classifier
    python pipeline/run_all.py --ml       # also train the classifier and use its maps
    python pipeline/run_all.py --from 4   # start at step 4 (after changing a threshold)
"""
import argparse
import importlib
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config as C

STEPS = ["01_grid", "02_nisar", "03_ancillary", "04_detect", "05_classify", "06_compare", "07_hillrisk", "08_stats"]

ap = argparse.ArgumentParser()
ap.add_argument("--ml", action="store_true", help="run 05_classify and use its maps")
ap.add_argument("--from", dest="start", type=int, default=1)
args = ap.parse_args()
if args.ml:
    C.DETECTOR = "ml"

for name in STEPS:
    n = int(name[:2])
    if n < args.start or (name == "05_classify" and not args.ml):
        continue
    t0 = time.time()
    print(f"\n===== {name} =====")
    importlib.import_module(name).main()
    print(f"({time.time() - t0:.0f} s)")
