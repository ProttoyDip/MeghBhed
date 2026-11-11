"""Step 5 of the label build: merge train sites and test points into labels/sites.csv.

Reads labels/build/train_sites.json and labels/build/test_points.json.
Train sites within 1 km of a test point are dropped, so training never sits next to the held-out points.

    python labels/build/write_sites.py .
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

root = Path(sys.argv[1]); here = Path(__file__).parent
t = Transformer.from_crs(4326, 32646, always_xy=True)

test = []
for o in json.loads((here / "test_points.json").read_text()):
    where = f"tree point {o['dist_m']} m from geocoded place, HAND {o['hand_m']} m"
    note = (f"{o['report_date']}: {o['quote']}; " if o["label"]
            else "upazila had general low-lying flooding reports but this place is not named; ") + where
    test.append(dict(lon=o["plon"], lat=o["plat"], label=o["label"], pairs="A" if o["label"] else "", source=o["source"],
                     set="test", place=o["place"], upazila=o["upazila"], confidence="medium" if o["label"] else "low", note=note))
test = pd.DataFrame(test)
tx, ty = t.transform(test.lon.values, test.lat.values)

train, dropped = [], 0
for s in json.loads((here / "train_sites.json").read_text()):
    x, y = t.transform(s["lon"], s["lat"])
    if np.min(np.hypot(tx - x, ty - y)) < 1000:
        dropped += 1
        continue
    if s["label"] == 1:
        note = (f"tree on HAND <= 5 m; {int(100 * s['fw_share'])}% of non-tree land within 100 m is new floodwater "
                "(16 Jul vs 7, 9, 19, 21 Jun)")
    else:
        note = "tree on HAND <= 5 m; no DSWx-S1 water within 1 km on 16 Jul or on 7, 9, 19, 21 Jun"
    train.append(dict(lon=s["lon"], lat=s["lat"], label=s["label"], pairs="A" if s["label"] else "",
                      source="DSWx-S1 new floodwater", set="train", place="", upazila=s["upazila"], confidence="medium", note=note))

cols = ["lon", "lat", "label", "pairs", "source", "set", "place", "upazila", "confidence", "note"]
d = pd.concat([pd.DataFrame(train), test], ignore_index=True)[cols]
d.to_csv(root / "labels" / "sites.csv", index=False)
print("train sites dropped for being within 1 km of a test point:", dropped)
print(d.groupby(["set", "label"]).size().to_string())
