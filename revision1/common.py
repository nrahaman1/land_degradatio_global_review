"""Shared paths, loaders and the Scopus Search API helper for the Revision 1 analyses.

The Scopus key is read from the SCOPUS_API_KEY environment variable (never stored in files).
"""
import csv, glob, json, os, re, time, hashlib
import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
CACHE = os.path.join(HERE, "cache")
# In the GitHub repository these scripts live in revision1/, next to data/ and scripts/;
# in the authors' working folder they live in Revision_1/Analysis.
IN_REPO = os.path.isdir(os.path.join(HERE, "..", "data"))
REPO = os.path.join(HERE, "..") if IN_REPO else os.path.join(HERE, "..", "..", "..", "Submission_to_Anthropocene", "GitHub_Repo")
WOS_DIR = os.path.join(HERE, "WoS_Data") if IN_REPO else os.path.join(HERE, "..", "WoS_Data")  # user-exported WoS files
XLSX = os.path.join(REPO, "data", "Consolidated_Method_Prediction_Excel_Updated.xlsx")
os.makedirs(OUT, exist_ok=True); os.makedirs(CACHE, exist_ok=True)

DIMS = ["Driver", "Process", "Impact", "Feedback Loop"]
QUERY_DIM = {"Q01": "Driver", "Q02": "Driver", "Q03": "Driver", "Q04": "Process", "Q05": "Process",
             "Q06": "Process", "Q07": "Process", "Q08": "Impact", "Q09": "Impact", "Q10": "Impact",
             "Q11": "Feedback Loop"}


def norm_title(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def norm_doi(s):
    return str(s).lower().strip().removeprefix("https://doi.org/") if isinstance(s, str) and s.strip() else None


def load_corpus():
    """(all_2472, dedup_2151) with eid / ntitle / ndoi helper columns."""
    a = pd.read_excel(XLSX, sheet_name="All_Data")
    u = pd.read_excel(XLSX, sheet_name="All_Data_Duplicate_Removed")
    for d in (a, u):
        d["eid"] = d.Link.str.extract(r"eid=(2-s2\.0-\d+)")[0]
        d["ntitle"] = d.Title.map(norm_title)
        d["ndoi"] = d.DOI.map(norm_doi)
    return a, u


def load_wos(drop_nonconforming=True):
    """All WoS exports, one row per (record, query). Drops book chapters / retracted items by default."""
    rows = []
    for f in sorted(glob.glob(os.path.join(WOS_DIR, "Q*", "*.txt"))):
        d = pd.read_csv(f, sep="\t", quoting=csv.QUOTE_NONE, dtype=str, encoding="utf-8-sig", index_col=False)
        d["Q"] = os.path.basename(os.path.dirname(f))[:3]
        rows.append(d)
    w = pd.concat(rows, ignore_index=True)
    w["Dimension"] = w.Q.map(QUERY_DIM)
    w["ntitle"] = w.TI.map(norm_title)
    w["ndoi"] = w.DI.map(norm_doi)
    if drop_nonconforming:
        w = w[~w.DT.str.contains("Book Chapter|Retract", na=False)]
    return w


def _get(params):
    for attempt in range(6):
        r = requests.get("https://api.elsevier.com/content/search/scopus", params=params, timeout=60,
                         headers={"X-ELS-APIKey": os.environ["SCOPUS_API_KEY"], "Accept": "application/json"})
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** attempt); continue
        if r.status_code >= 400:
            raise RuntimeError(f"Scopus {r.status_code}: {r.text[:300]} | query={params['query'][:200]}")
        return r.json()["search-results"]
    raise RuntimeError("Scopus API kept failing")


def scopus_search(query, fields=None, count_only=False, use_cache=True):
    """Scopus Search API (STANDARD view). Returns (total, entries).

    Our key works off-campus, which allows only 25 records per request and start+count <= 5000,
    so larger result sets are split by publication year (PUBYEAR) automatically.
    """
    tag = hashlib.md5(f"{query}|{fields}|{count_only}".encode()).hexdigest()
    cf = os.path.join(CACHE, f"scopus_{tag}.json")
    if use_cache and os.path.exists(cf):
        with open(cf, encoding="utf-8") as fh:
            c = json.load(fh)
        return c["total"], c["entries"]
    params = {"query": query, "count": 25, "start": 0} | ({"field": fields} if fields else {})
    sr = _get(params)
    total = int(sr["opensearch:totalResults"])
    entries = [e for e in sr.get("entry", []) if "error" not in e]
    if not count_only:
        if total > 5000:  # split by year: <=1999, then single years
            entries = []
            for yq in ["PUBYEAR < 2000"] + [f"PUBYEAR = {y}" for y in range(2000, 2027)]:
                entries += scopus_search(f"({query}) AND {yq}", fields, use_cache=use_cache)[1]
        else:
            while len(entries) < total:
                params["start"] = len(entries)
                batch = [e for e in _get(params).get("entry", []) if "error" not in e]
                if not batch:
                    break
                entries += batch
                time.sleep(0.12)
    with open(cf, "w", encoding="utf-8") as fh:
        json.dump({"query": query, "total": total, "entries": entries}, fh)
    return total, entries
