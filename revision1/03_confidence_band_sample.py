"""Reviewer 2, comment (iv): spot-check of predictions kept automatically (confidence >= 0.5).

Draws a fixed random sample of 20 abstracts from the medium band (0.5 <= conf < 0.9) and 20 from the
high band (conf >= 0.9) of the analytic corpus, excluding the 503 reference abstracts (seen in training).
Writes outputs/03_confidence_band_audit.xlsx for manual checking: one row per abstract with the predicted
category; the checker fills Checked_Category and the script `--score` mode reports error rates per band.
"""
import sys
import pandas as pd
from common import load_corpus, OUT

FILE = f"{OUT}/03_confidence_band_audit.xlsx"


def draw():
    a, u = load_corpus()
    pool = u[u.Method_Category_Manual.isna()].copy()
    pool["band"] = pd.cut(pool.Prediction_Confidence, [0.5, 0.9, 1.0001], right=False, labels=["medium (0.5-0.9)", "high (>=0.9)"])
    s = (pool.dropna(subset=["band"]).groupby("band", observed=True, group_keys=False)
         .apply(lambda g: g.sample(20, random_state=2026)))
    s = s[["band", "eid", "Title", "Year", "Abstract", "Prediction_Confidence",
           "Predicted_Method_Category_With_Manual_Validation"]].rename(
        columns={"Predicted_Method_Category_With_Manual_Validation": "Predicted_Category"})
    s["Checked_Category"] = ""; s["Checked_Family"] = ""; s["Note"] = ""
    s.to_excel(FILE, index=False)
    print(f"wrote {len(s)} rows to {FILE}")


def score():
    sys.path.insert(0, ".")
    from importlib import import_module
    fam = import_module("02_classifier_validation").fam
    s = pd.read_excel(FILE)
    s["ok_20"] = s.Predicted_Category.map(lambda x: str(x).strip()) == s.Checked_Category.map(lambda x: str(x).strip())
    s["ok_family"] = s.Predicted_Category.map(fam) == s.Checked_Family
    r = s.groupby("band").agg(n=("ok_20", "size"), correct_20class=("ok_20", "sum"), correct_family=("ok_family", "sum"))
    r["pct_20class"] = (100 * r.correct_20class / r.n).round(0)
    r["pct_family"] = (100 * r.correct_family / r.n).round(0)
    r.to_csv(f"{OUT}/03_confidence_band_scores.csv")
    print(r.to_string())


if __name__ == "__main__":
    score() if "--score" in sys.argv else draw()
