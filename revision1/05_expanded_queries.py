"""Reviewer 2, comment (iii): are the thematic shares an artefact of restrictive query wording?

Compares, in Scopus (same fields, TITLE-ABS-KEY), the original Table 1 query terms with expanded,
synonym-based query terms for each dimension. Shares are computed from hit counts only:
    share(d) = hits(LD AND d) / hits(LD AND (D1 OR D2 OR D3 OR D4))    [multi-label, can sum > 100%]
and, for context, as a share of all "land degradation" records (the wider literature).
All searches use the corpus filters: Article or Conference paper, English, published <= 2024
(the original corpus was retrieved in Feb 2025, so 2025 is excluded for comparability).
Outputs: outputs/05_expanded_query_counts.csv, outputs/05_expanded_query_terms.csv
"""
import pandas as pd
from common import scopus_search, OUT

LD = 'TITLE-ABS-KEY("land degradation")'
FILTERS = "DOCTYPE(ar OR cp) AND LANGUAGE(english) AND PUBYEAR < 2025"

ORIGINAL = {  # union of the Table 1 sub-queries of each dimension
    "Driver": "drivers AND factors AND (human OR natural)",
    "Process": "process AND (physical OR chemical OR biological)",
    "Impact": "impact AND (environmental OR socioeconomic)",
    "Feedback Loop": "feedback AND loop",
}
EXPANDED = {
    "Driver": '(driver* OR "driving force*" OR "driving factor*" OR determinant* OR "underlying cause*" '
              'OR "proximate cause*" OR "root cause*" OR "causal factor*")',
    "Process": '(process* OR mechanism* OR pathway*) AND (physical OR chemical OR biological OR biophysical '
               'OR biogeochemical OR hydrolog* OR geomorpholog* OR pedolog*)',
    "Impact": '(impact* OR effect* OR consequence* OR outcome*) AND (environmental OR ecological OR socioeconomic '
              'OR "socio-economic" OR economic OR social OR livelihood* OR "food security" OR "ecosystem service*")',
    "Feedback Loop": '(feedback* OR "self-reinforc*" OR "reinforcing loop*" OR "vicious cycle*" OR "vicious circle*" '
                     'OR "downward spiral*" OR "poverty trap*")',
}


def hits(terms):
    q = f"{LD} AND TITLE-ABS-KEY({terms}) AND {FILTERS}" if terms else f"{LD} AND {FILTERS}"
    return scopus_search(q, count_only=True)[0]


def main():
    total_ld = hits(None)
    rows = []
    for name, qs in (("original (Table 1)", ORIGINAL), ("expanded (synonyms)", EXPANDED)):
        union = hits(" OR ".join(f"({v})" for v in qs.values()))
        for d, t in qs.items():
            n = hits(t)
            rows.append({"query set": name, "dimension": d, "hits": n,
                         "share of union %": round(100 * n / union, 1),
                         "share of all LD records %": round(100 * n / total_ld, 1),
                         "union": union, "all LD records": total_ld})
    for d in ORIGINAL:  # how much of the expanded theme the original wording already captures
        both = hits(f"({ORIGINAL[d]}) AND ({EXPANDED[d]})")
        rows.append({"query set": "original AND expanded", "dimension": d, "hits": both})
    # upper bracket for feedback: also count non-linear-dynamics vocabulary
    broad_fb = EXPANDED["Feedback Loop"][:-1] + ' OR "tipping point*" OR "regime shift*" OR threshold*)'
    n = hits(broad_fb); union = hits(" OR ".join(f"({v})" for v in {**EXPANDED, "Feedback Loop": broad_fb}.values()))
    rows.append({"query set": "expanded + tipping points/regime shifts/thresholds", "dimension": "Feedback Loop",
                 "hits": n, "share of union %": round(100 * n / union, 1),
                 "share of all LD records %": round(100 * n / total_ld, 1), "union": union, "all LD records": total_ld})
    out = pd.DataFrame(rows)
    out.to_csv(f"{OUT}/05_expanded_query_counts.csv", index=False)
    pd.DataFrame({"original": ORIGINAL, "expanded": EXPANDED}).to_csv(f"{OUT}/05_expanded_query_terms.csv")
    print(f'All "land degradation" records (filters applied): {total_ld}')
    print(out.pivot(index="dimension", columns="query set", values="hits").to_string())
    print(out.dropna(subset=["share of union %"]).pivot(index="dimension", columns="query set",
                                                        values=["share of union %", "share of all LD records %"]).to_string())


if __name__ == "__main__":
    main()
