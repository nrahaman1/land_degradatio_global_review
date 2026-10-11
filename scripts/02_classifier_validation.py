"""Reviewer 1 (methods clarity) and Reviewer 2, comments (ii) and (iv): classifier validation.

  A. The production pipeline (SBERT all-MiniLM-L6-v2 + MLP 128/64, 20 classes), cross-validated on the 503
     reference abstracts, scored at 20-class level AND after collapsing its predictions to the six families.
  B. Calibration: held-out accuracy by confidence band (<0.5, 0.5-0.7, 0.7-0.9, >=0.9).
  C. The family-level model of revalidate_method_families.py (all-mpnet-base-v2 + QA spans, LinearSVC),
     with folds grouped by title so the 13 duplicated abstracts cannot leak between train and test.
  D. Agreement between the corpus labels used in the paper (MLP 20-class + manual review, mapped to families)
     and an independent prediction of the corpus by the family-level model.
  E. Method-family mix of Web of Science-only records vs the Scopus corpus (same abstract-only model).
All CV uses 5 folds, grouped by normalised title; scores are mean and range over 5 seeds.
"""
import os, re, sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
from sklearn.neural_network import MLPClassifier
from sklearn.svm import LinearSVC
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.metrics import accuracy_score, f1_score, cohen_kappa_score, precision_recall_fscore_support
from common import load_corpus, load_wos, OUT, CACHE, REPO

sys.path.insert(0, os.path.join(REPO, "scripts"))
from revalidate_method_families import FAMILY  # the published 20-class -> family mapping

SEEDS = [42, 1, 7, 11, 2024]
FAMS = ["Experimental & laboratory", "Geospatial monitoring", "Statistical & econometric",
        "Qualitative, mixed & conceptual", "Dynamic & predictive modeling", "Policy & LDN framework"]


def clean(x):
    return re.sub(r"\s+", " ", str(x).replace("–", "-").replace("â€“", "-")).strip()


def fam(x):
    x = clean(x)
    return FAMILY.get(x) or ("Dynamic & predictive modeling" if ("Coupled" in x or "Systems" in x) else None)


_MODELS = {}


def embed(name, texts, tag):
    f = os.path.join(CACHE, f"emb_{tag}.npy")
    if os.path.exists(f):
        e = np.load(f)
        if len(e) == len(texts):
            return e
    model = _MODELS.setdefault(name, SentenceTransformer(name) if name not in _MODELS else None)
    e = model.encode(list(texts), batch_size=16, show_progress_bar=False)
    np.save(f, e)
    return e


def scores(y, p):
    return dict(acc=accuracy_score(y, p), macro_f1=f1_score(y, p, average="macro"),
                weighted_f1=f1_score(y, p, average="weighted"), kappa=cohen_kappa_score(y, p))


def summarise(rows):
    d = pd.DataFrame(rows)
    return d.agg(["mean", "min", "max"]).round(3)


def mlp():
    return MLPClassifier(hidden_layer_sizes=(128, 64), activation="relu", solver="adam", alpha=1e-4,
                         learning_rate_init=1e-3, max_iter=1000, random_state=42)


def main():
    a, u = load_corpus()
    a["Abstract"] = a.Abstract.fillna("")
    lab = a[a.Method_Category_Manual.notna()].reset_index(drop=True)
    y20 = lab.Method_Category_Manual.map(clean).values
    yfam = lab.Method_Category_Manual.map(fam).values
    groups = pd.factorize(lab.ntitle)[0]
    print(f"Reference set: {len(lab)} abstracts, {len(set(y20))} classes, {lab.ntitle.nunique()} unique titles")

    # ---------- A + B: production pipeline (MiniLM + MLP, 20 classes) ----------
    X_mini = embed("all-MiniLM-L6-v2", lab.Abstract, "minilm_ref")
    rowsA20, rowsAfam, calib = [], [], []
    for s in SEEDS:
        cv = StratifiedGroupKFold(5, shuffle=True, random_state=s)
        proba = cross_val_predict(mlp(), X_mini, y20, cv=cv, groups=groups, method="predict_proba")
        classes = np.unique(y20)  # cross_val_predict orders columns by sorted class labels
        p20 = classes[proba.argmax(1)]
        conf = proba.max(1)
        rowsA20.append(scores(y20, p20))
        pfam = np.array([fam(c) for c in p20])
        rowsAfam.append(scores(yfam, pfam))
        band = pd.cut(conf, [0, .5, .7, .9, 1.0001], right=False, labels=["<0.5", "0.5-0.7", "0.7-0.9", ">=0.9"])
        calib.append(pd.DataFrame({"band": band, "correct20": p20 == y20, "correct_fam": pfam == yfam})
                     .groupby("band", observed=False).agg(n=("correct20", "size"), acc_20class=("correct20", "mean"),
                                                          acc_family=("correct_fam", "mean")))
    A20, Afam = summarise(rowsA20), summarise(rowsAfam)
    B = pd.concat(calib).groupby(level=0, observed=False).mean().round(3)

    # ---------- C: family model (mpnet + spans, LinearSVC), title-grouped CV ----------
    for c in ["Method_Answer", "Model_Answer", "Technique_Answer"]:
        a[c] = a[c].fillna("")
    a["combo"] = (a.Abstract + ". Method: " + a.Method_Answer.astype(str) + ". Model: " + a.Model_Answer.astype(str)
                  + ". Technique: " + a.Technique_Answer.astype(str))
    X_all_combo = embed("all-mpnet-base-v2", a.combo, "mpnet_combo_all2472")
    lab_idx = a.index[a.Method_Category_Manual.notna()]
    X_mp = X_all_combo[lab_idx]
    rowsC, perfam = [], []
    for s in SEEDS:
        cv = StratifiedGroupKFold(5, shuffle=True, random_state=s)
        p = cross_val_predict(LinearSVC(C=1), X_mp, yfam, cv=cv, groups=groups)
        rowsC.append(scores(yfam, p))
        P, R, F, N = precision_recall_fscore_support(yfam, p, labels=FAMS, zero_division=0)
        perfam.append(pd.DataFrame({"precision": P, "recall": R, "f1": F, "ref_n": N}, index=FAMS))
    C = summarise(rowsC)
    Cfam = pd.concat(perfam).groupby(level=0).mean().reindex(FAMS).round(2)
    Cfam["ref_n"] = Cfam.ref_n.astype(int)

    # ---------- D: agreement on the corpus ----------
    svc = LinearSVC(C=1).fit(X_mp, yfam)
    first = a[a.eid.isin(u.eid)].drop_duplicates("eid")  # the 2,151-article analytic corpus
    p_corpus = svc.predict(X_all_combo[first.index])
    used = first.Predicted_Method_Category_With_Manual_Validation.map(fam).values
    D = {"n": len(first), "agreement_pct": round(100 * (p_corpus == used).mean(), 1),
         "kappa": round(cohen_kappa_score(used, p_corpus), 3)}
    shares = pd.DataFrame({"paper (MLP + manual review)": pd.Series(used).value_counts(normalize=True),
                           "family model": pd.Series(p_corpus).value_counts(normalize=True)}).reindex(FAMS).mul(100).round(1)
    unl = ~first.Method_Category_Manual.notna().values
    D["agreement_unlabelled_only_pct"] = round(100 * (p_corpus[unl] == used[unl]).mean(), 1)

    # ---------- E: WoS-only vs Scopus corpus, abstract-only mpnet model ----------
    X_abs_ref = embed("all-mpnet-base-v2", lab.Abstract, "mpnet_abs_ref")
    svc_abs = LinearSVC(C=1).fit(X_abs_ref, yfam)
    w = load_wos().drop_duplicates("UT")
    only_ut = set(pd.read_csv(f"{OUT}/01_wos_only_records.csv").UT)
    wo = w[w.UT.isin(only_ut) & w.AB.notna()]
    X_wo = embed("all-mpnet-base-v2", wo.AB, "mpnet_abs_wosonly")
    X_sc = embed("all-mpnet-base-v2", first.Abstract, "mpnet_abs_corpus")
    E = pd.DataFrame({"Scopus corpus": pd.Series(svc_abs.predict(X_sc)).value_counts(normalize=True),
                      f"WoS-only (n={len(wo)})": pd.Series(svc_abs.predict(X_wo)).value_counts(normalize=True)}
                     ).reindex(FAMS).mul(100).round(1)

    # ---------- write ----------
    with pd.ExcelWriter(f"{OUT}/02_classifier_validation.xlsx") as xw:
        A20.to_excel(xw, "A_MLP_20class_CV"); Afam.to_excel(xw, "A_MLP_collapsed_to_family")
        B.to_excel(xw, "B_calibration_by_band"); C.to_excel(xw, "C_family_model_CV")
        Cfam.to_excel(xw, "C_per_family"); shares.to_excel(xw, "D_corpus_shares")
        pd.Series(D).to_excel(xw, "D_agreement"); E.to_excel(xw, "E_wos_only_families")
    for name, obj in [("A. MLP 20-class (title-grouped 5-fold CV, 5 seeds)", A20),
                      ("A. MLP predictions collapsed to families", Afam),
                      ("B. Held-out accuracy by confidence band (MLP)", B),
                      ("C. Family model (mpnet+spans, LinearSVC)", C), ("C. per family", Cfam),
                      ("D. Corpus family shares", shares), ("D. Agreement", pd.Series(D)),
                      ("E. Family mix, abstract-only model", E)]:
        print(f"\n== {name}\n{obj.to_string()}")


if __name__ == "__main__":
    main()
