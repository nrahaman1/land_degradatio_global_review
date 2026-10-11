"""Harmonised thematic counts (Section 4.1, Figure 4) on the 2,151-article analytic corpus.

An article is counted once in EVERY dimension whose query retrieved it (multi-label), so shares can sum
to >100%. The manuscript's single-assignment shares (first query wins) are reported alongside.
The Scopus corpus was retrieved 17-19 Feb 2025, so 2025 is partial and is excluded from the trend figure.
Outputs: outputs/04_theme_counts_by_year.csv, outputs/04_theme_shares.csv, outputs/Figure_4_revised.tif
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from common import load_corpus, OUT, DIMS

COLORS = {"Driver": "#e8000b", "Feedback Loop": "#4cc9f0", "Impact": "#2ecc40", "Process": "#ffb000"}
LABELS = {"Driver": "Drivers", "Feedback Loop": "Feedback loops", "Impact": "Impacts", "Process": "Processes"}


def main():
    a, u = load_corpus()
    dims_of = a.groupby("ntitle").Dimension.agg(set)
    u["dims"] = u.ntitle.map(dims_of)
    long = u[["eid", "Year", "dims"]].explode("dims").rename(columns={"dims": "Dimension"})

    counts = pd.crosstab(long.Year, long.Dimension).reindex(columns=DIMS, fill_value=0)
    counts = counts.reindex(range(counts.index.min(), counts.index.max() + 1), fill_value=0)  # show empty years as 0
    counts["Articles"] = u.groupby("Year").size().reindex(counts.index, fill_value=0)
    shares_year = counts[DIMS].div(counts.Articles, axis=0).mul(100).round(1)
    counts.join(shares_year.add_suffix(" %")).to_csv(f"{OUT}/04_theme_counts_by_year.csv")

    multi = {d: round(100 * u.dims.map(lambda s: d in s).mean(), 1) for d in DIMS}
    single = {d: round(100 * (u.Dimension == d).mean(), 1) for d in DIMS}
    pd.DataFrame({"multi-label (counted in each dimension retrieved)": multi,
                  "single-assignment (manuscript)": single}).T.to_csv(f"{OUT}/04_theme_shares.csv")
    print(f"n = {len(u)} articles; {(u.dims.map(len) > 1).sum()} retrieved by queries of >1 dimension")
    print("multi-label shares :", multi)
    print("single-assignment  :", single)
    for y in (2000, 2010, 2012, 2015, 2020, 2024):
        print(y, "impact share", shares_year.loc[y, "Impact"], "| n =", counts.loc[y, "Articles"])
    print("impact share 2015-2024 range:", shares_year.loc[2015:2024, "Impact"].min(), "-", shares_year.loc[2015:2024, "Impact"].max())

    c = counts.loc[:2024]
    fig, ax = plt.subplots(figsize=(11.7, 5.4), dpi=300)
    for d in ["Driver", "Feedback Loop", "Impact", "Process"]:
        ax.plot(c.index, c[d], "-o", color=COLORS[d], ms=5, lw=1.6, label=LABELS[d])
    ax.set_xlabel("Publication year"); ax.set_ylabel("Number of articles")
    ax.set_xlim(c.index.min() - 0.5, 2024.5); ax.set_ylim(0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14))
    fig.tight_layout()
    fig.savefig(f"{OUT}/Figure_4_revised.tif", dpi=300, pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(f"{OUT}/Figure_4_revised.png", dpi=120)


if __name__ == "__main__":
    main()
