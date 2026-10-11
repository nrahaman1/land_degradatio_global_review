"""Reviewer 2, comment (i): sensitivity of the corpus to the choice of database.

Re-runs the 11 Table 1 queries in Web of Science Core Collection (exports in ../WoS_Data) and compares:
  1. record-level overlap with the Scopus analytic corpus (DOI, then normalised title);
  2. whether WoS-only records are indexed in Scopus at all, and whether they match the Scopus queries today;
  3. thematic shares (unique articles, counted once per dimension retrieved) in each database.
Outputs: outputs/01_*.csv and a printed summary.
"""
import pandas as pd
from common import load_corpus, load_wos, scopus_search, norm_title, OUT, DIMS

SCOPUS_QUERIES = [
    '"land degradation" AND drivers AND human AND factors AND NOT natural',
    '"land degradation" AND drivers AND natural AND factors AND NOT human',
    '"land degradation" AND drivers AND natural AND factors AND human',
    '"land degradation" AND process AND physical',
    '"land degradation" AND process AND chemical',
    '"land degradation" AND process AND biological',
    '"land degradation" AND impact AND environmental AND NOT socioeconomic',
    '"land degradation" AND impact AND socioeconomic AND NOT environmental',
    '"land degradation" AND impact AND socioeconomic AND environmental',
    '"land degradation" AND feedback AND loop',
]  # Q07 (process AND all three) is a subset of Q04-Q06, so it adds nothing to the union
ANY_QUERY = " OR ".join(f"TITLE-ABS-KEY({q})" for q in SCOPUS_QUERIES)


def theme_shares(df, id_col):
    """% of unique articles retrieved by >=1 query of each dimension (multi-label; sums >100%)."""
    n = df[id_col].nunique()
    return {d: round(100 * df.loc[df.Dimension == d, id_col].nunique() / n, 1) for d in DIMS} | {"n_unique": n}


def main():
    a, u = load_corpus()
    w_all = load_wos(drop_nonconforming=False)
    w = load_wos()
    print(f"WoS rows {len(w_all)} -> {len(w)} after dropping book chapters/retracted; unique UT {w.UT.nunique()}")

    # --- 1. record-level matching (one row per unique WoS record) -------------------------
    wu = w.drop_duplicates("UT").copy()
    sc_doi = set(u.ndoi.dropna()); sc_title = set(u.ntitle)
    wu["in_scopus_corpus"] = wu.ndoi.isin(sc_doi) | wu.ntitle.isin(sc_title)
    w_doi = set(wu.ndoi.dropna()); w_title = set(wu.ntitle)
    u["in_wos"] = u.ndoi.isin(w_doi) | u.ntitle.isin(w_title)

    # --- 2. are WoS-only records indexed in Scopus, and do they match the Scopus queries today? ---
    only = wu[~wu.in_scopus_corpus].copy()
    # Old SICI-style DOIs (with <>;() etc.) break Scopus syntax, so those records are looked up by exact title.
    safe = only.ndoi.fillna("").str.fullmatch(r"[a-z0-9./_\-]+")
    terms = [f'DOI("{d}")' for d in only.loc[safe, "ndoi"]] + [f'TITLE("{t}")' for t in only.loc[~safe, "ntitle"]]
    found = {"indexed": set(), "matched": set()}
    for i in range(0, len(terms), 8):  # small batches keep the URL under the server limit
        q = " OR ".join(terms[i:i + 8])
        for kind, query in (("indexed", q), ("matched", f"({q}) AND ({ANY_QUERY})")):
            for e in scopus_search(query, fields="prism:doi,dc:title")[1]:
                found[kind] |= {str(e.get("prism:doi", "")).lower(), norm_title(e.get("dc:title", ""))}
    only["indexed_in_scopus"] = only.ndoi.isin(found["indexed"]) | only.ntitle.isin(found["indexed"])
    only["matches_scopus_query_today"] = only.ndoi.isin(found["matched"]) | only.ntitle.isin(found["matched"])

    # --- 3. thematic shares ------------------------------------------------------------------
    a2 = a.copy(); a2["id"] = a2.ntitle  # Scopus: per-query dimension labels before de-duplication
    sh = pd.DataFrame({
        "Scopus corpus (2,472 query hits -> unique titles)": theme_shares(a2, "id"),
        "Scopus corpus, single-assignment (2,151; as in manuscript)": {
            **{d: round(100 * (u.Dimension == d).mean(), 1) for d in DIMS}, "n_unique": len(u)},
        "Web of Science (same 11 queries)": theme_shares(w, "UT"),
    }).T
    sh.to_csv(f"{OUT}/01_theme_shares_by_database.csv")

    # The Scopus corpus was retrieved 17-19 Feb 2025, so 2025 is only partly covered; the <=2024 window is
    # the like-for-like comparison.
    def overlap(uu, ww, oo):
        return {
            "scopus_corpus_records": len(uu),
            "wos_unique_records": len(ww),
            "scopus_corpus_found_in_wos": int(uu.in_wos.sum()),
            "scopus_corpus_found_in_wos_pct": round(100 * uu.in_wos.mean(), 1),
            "wos_records_found_in_scopus_corpus_pct": round(100 * ww.in_scopus_corpus.mean(), 1),
            "wos_only_records": int((~ww.in_scopus_corpus).sum()),
            "wos_only_not_indexed_in_scopus": int((~oo.indexed_in_scopus).sum()),
            "wos_only_indexed_but_not_matching_scopus_queries": int((oo.indexed_in_scopus & ~oo.matches_scopus_query_today).sum()),
            "wos_only_matching_scopus_queries_today": int(oo.matches_scopus_query_today.sum()),
            "jaccard_overlap_pct": round(100 * uu.in_wos.sum() / (len(uu) + (~ww.in_scopus_corpus).sum()), 1),
        }
    py = pd.to_numeric(wu.PY, errors="coerce"); opy = pd.to_numeric(only.PY, errors="coerce")
    only_summary = pd.DataFrame({
        "all years": overlap(u, wu, only),
        "published <= 2024": overlap(u[u.Year <= 2024], wu[py <= 2024], only[opy <= 2024]),
    })
    only_summary.to_csv(f"{OUT}/01_overlap_summary.csv")
    wu.loc[~wu.in_scopus_corpus, ["UT", "DI", "TI", "PY", "DT", "Q", "Dimension"]].merge(
        only[["UT", "indexed_in_scopus", "matches_scopus_query_today"]], on="UT", how="left"
    ).to_csv(f"{OUT}/01_wos_only_records.csv", index=False)
    yr = pd.crosstab(pd.to_numeric(wu.PY, errors="coerce"), wu.in_scopus_corpus)
    yr.to_csv(f"{OUT}/01_overlap_by_year.csv")

    print(only_summary.to_string())
    print("\nTheme shares (% of unique articles; multi-label rows can sum >100):\n", sh.to_string())
    print("\nWoS-only records by publication year (last 8 years):\n", yr.tail(8).to_string())


if __name__ == "__main__":
    main()
