"""
Re-validation of the methodological classifier at the level of six coarse
method families (Section 3.3.11 of the manuscript).

The original 20-class scheme is too fine-grained for the size of the manually
labelled reference set (~504 abstracts; several classes with <5 examples), and
several of the 20 classes are not mutually exclusive. A held-out evaluation of
the 20-class model gives only ~0.36-0.39 accuracy (macro-F1 ~0.26), and the
model is poorly calibrated. This script collapses the 20 classes into six
interpretable method families and reports honest, reproducible metrics
(5-fold stratified cross-validation): accuracy, macro/weighted F1, Cohen's
kappa, a per-family classification report, and a confusion matrix.

It is self-contained against the data shipped in this repository:
    ../data/Consolidated_Method_Prediction_Excel_Updated.xlsx  (sheet "All_Data")
which contains the manually assigned labels (Method_Category_Manual) together
with the abstract text and the RoBERTa-extracted method/model/technique spans.

Requirements: pandas, numpy, scikit-learn, sentence-transformers.
"""
import os
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
from sklearn.svm import LinearSVC
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import (accuracy_score, f1_score, cohen_kappa_score,
                             classification_report, confusion_matrix)
from sklearn.preprocessing import LabelEncoder

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "Consolidated_Method_Prediction_Excel_Updated.xlsx")
SHEET = "All_Data"

FAMILY = {
    "Wet lab analysis": "Experimental & laboratory",
    "Remote Sensing / GIS Analysis": "Geospatial monitoring",
    "Traditional Spatial Temporal Analysis": "Geospatial monitoring",
    "Non-parametric Spatial Temporal Analysis": "Geospatial monitoring",
    "Trend Analysis": "Geospatial monitoring",
    "Spatial Cluster Analysis": "Geospatial monitoring",
    "Parametric Statistical Analysis": "Statistical & econometric",
    "Econometric Analysis": "Statistical & econometric",
    "Factor Analysis": "Statistical & econometric",
    "PCA": "Statistical & econometric",
    "Qualitative Analysis": "Qualitative, mixed & conceptual",
    "Mixed Method": "Qualitative, mixed & conceptual",
    "Conceptual / Framework Development": "Qualitative, mixed & conceptual",
    "Traditional Systematic Review": "Qualitative, mixed & conceptual",
    "Systematic Review": "Qualitative, mixed & conceptual",
    "Machine Learning": "Dynamic & predictive modeling",
    "Custom Model": "Dynamic & predictive modeling",
    "Integrated Environmental Modeling": "Dynamic & predictive modeling",
    "Scenario-Based Simulation / Forecasting": "Dynamic & predictive modeling",
    "Coupled Human-Natural Systems Modeling": "Dynamic & predictive modeling",
    "Systems / Network Analysis": "Dynamic & predictive modeling",
    "LDN Framework": "Policy & LDN framework",
}


def to_family(x):
    if not isinstance(x, str):
        return None
    x = x.replace("�", "-").strip()
    if x in FAMILY:
        return FAMILY[x]
    if "Coupled" in x or "Systems" in x:
        return "Dynamic & predictive modeling"
    return None


def main():
    df = pd.read_excel(DATA, sheet_name=SHEET)
    for c in ["Abstract", "Method_Answer", "Model_Answer", "Technique_Answer"]:
        df[c] = df[c].fillna("")
    df["combo"] = (df["Abstract"].astype(str)
                   + ". Method: " + df["Method_Answer"].astype(str)
                   + ". Model: " + df["Model_Answer"].astype(str)
                   + ". Technique: " + df["Technique_Answer"].astype(str))
    df["family"] = df["Method_Category_Manual"].apply(to_family)
    tr = df[df["family"].notna()].copy()

    model = SentenceTransformer("all-mpnet-base-v2")
    X = model.encode(tr["combo"].astype(str).tolist(), show_progress_bar=True)
    y = LabelEncoder().fit_transform(tr["family"])
    le = LabelEncoder().fit(tr["family"])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred = cross_val_predict(LinearSVC(C=1), X, y, cv=cv)

    print(f"Labelled reference abstracts: {len(y)}")
    print(f"Accuracy      : {accuracy_score(y, y_pred):.3f}")
    print(f"Macro F1      : {f1_score(y, y_pred, average='macro'):.3f}")
    print(f"Weighted F1   : {f1_score(y, y_pred, average='weighted'):.3f}")
    print(f"Cohen's kappa : {cohen_kappa_score(y, y_pred):.3f}\n")
    print(classification_report(y, y_pred, target_names=le.classes_, digits=3))
    print("Confusion matrix (rows=true, cols=pred):")
    print(list(le.classes_))
    print(confusion_matrix(y, y_pred))


if __name__ == "__main__":
    main()
