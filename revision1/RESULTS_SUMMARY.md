# Revision 1 — new analyses and what they mean for the manuscript

All scripts are in this folder (`01_…py` to `06_…py`, shared helpers in `common.py`); every number below is
written to `outputs/`. The Scopus key is read from the `SCOPUS_API_KEY` environment variable and is not stored
in any file. Run order: `01` → `06` (01 must run before 02).

**Data facts established during the analyses**
- The Scopus corpus was retrieved **17–19 February 2025** (export file dates), so "2025" contains only 30 records
  (seven weeks). The manuscript should give the retrieval date and describe coverage as 1982 – February 2025.
- The final labels of the 503 reference abstracts are the manual labels (correct). The reported mean confidence
  of 0.83 includes those 503 near-certain predictions (mean 0.98); for the 1,969 unlabelled abstracts it is **0.79**.

---

## Reviewer 2 (i) — single database (Scopus) → `01_wos_scopus_overlap.py`

Same 11 queries re-run in Web of Science Core Collection on 9 Oct 2026 (Article/Proceedings Paper, English,
PY ≤ 2025; book chapters and 3 retracted items removed) → **1,830 unique WoS records**.

| | all years | published ≤ 2024 (like-for-like) |
|---|---|---|
| Scopus corpus records | 2,151 | 2,121 |
| … also retrieved by the WoS queries | 1,100 (51.1%) | 1,077 (50.8%) |
| WoS records also in Scopus corpus | 60.1% | 67.0% |
| WoS-only records | 730 | 526 |
|  – not indexed in Scopus at all | 116 | 114 |
|  – in Scopus but not matching the Scopus wording (field differences, e.g. WoS *Keywords Plus*) | 416 | 366 |
|  – in Scopus and matching our queries today (= missed by our Feb-2025 retrieval) | 198 (mostly 2025) | **46 (≈2%)** |

**Thematic shares are stable across databases** (% of unique articles, an article counted in every dimension that retrieved it):

| | Driver | Process | Impact | Feedback |
|---|---|---|---|---|
| Scopus corpus | 5.5 | 21.5 | 78.3 | 0.7 |
| Web of Science, same queries | 7.9 | 21.8 | 75.1 | 1.1 |

**Method-family mix is also stable**: WoS-only records (n = 727, same abstract-only classifier) vs Scopus corpus —
experimental 14.7 vs 17.0%, geospatial 27.2 vs 24.8%, statistical 6.9 vs 7.5%, qualitative/mixed/conceptual 31.8 vs 34.3%,
dynamic & predictive 19.4 vs 16.3%. Database bias does not materially propagate into the method results.

**Take-away for the paper:** record-level overlap between databases is only ~50%, but the thematic and
methodological proportions — the paper's actual findings — differ by ≤ 3 percentage points.

## Reviewer 2 (iii) — restrictive Boolean wording → `05_expanded_query_counts.csv`

Scopus hit counts, TITLE-ABS-KEY, same filters, published ≤ 2024. All "land degradation" records: **9,974**.
Share = hits of the dimension ÷ hits of the union of the four dimensions (multi-label).

| Dimension | Original (Table 1) | Expanded synonyms | Expanded + "tipping point / regime shift / threshold" |
|---|---|---|---|
| Impact | 78.8% (1,579) | **79.5%** (3,931) | — |
| Process | 20.8% (417) | **19.8%** (977) | — |
| Driver | 5.7% (115) | **20.2%** (1,000) | — |
| Feedback | 0.7% (15) | **3.4%** (166) | **7.7%** (387) |
| Union | 2,004 | 4,946 | 5,052 |

Expanded terms are in `05_expanded_query_terms.csv` (e.g. drivers: driver*, "driving force*", determinant*,
"underlying/proximate/root cause*"; feedback: feedback*, "self-reinforc*", "vicious cycle/circle*", "downward spiral*", "poverty trap*").
Every original hit is also an expanded hit (original ⊂ expanded for all four dimensions).

**Take-away — this changes one headline number and must be reported honestly:**
- Impact dominance (~79%) and the process share (~20%) are **robust** to query wording.
- Feedback-focused research is the **least represented dimension under every definition** (0.7–7.7%).
- The **drivers share is not robust**: 5.7% with the original wording, ~20% with synonyms — comparable to processes.
  The manuscript should stop presenting "5% drivers" as a finding; say drivers are under-represented *relative to impacts*
  and that their exact share depends on terminology.

## Reviewer 2 (ii) + Reviewer 1 (methods clarity) — classifier → `02_classifier_validation.xlsx`

All cross-validation: 5 folds **grouped by title** (the 503 reference abstracts contain 13 duplicated titles across
queries; grouping prevents train/test leakage), mean and range over 5 seeds. n = **503** throughout.

| Model (what it is used for) | Accuracy | Weighted F1 | Macro F1 | κ |
|---|---|---|---|---|
| A. Production MLP, 20 classes (produced the corpus labels) | 0.37 (0.35–0.38) | 0.36 | 0.24 | 0.31 |
| A. Same MLP predictions collapsed to 6 families | 0.56 (0.56–0.57) | 0.56 | 0.49 | 0.44 |
| C. Family model (mpnet + QA spans, linear SVM) | **0.64 (0.64–0.64)** | **0.62** | 0.51 | **0.53** |

Per family (model C; replaces Table 3, whose Ref n must sum to **503**: dynamic & predictive = **114**, not 115):

| Family | Ref n | Precision | Recall | F1 | Corpus share |
|---|---|---|---|---|---|
| Qualitative, mixed & conceptual | 135 | 0.73 | 0.80 | 0.77 | 30.5% |
| Geospatial monitoring | 129 | 0.58 | 0.69 | 0.63 | 24.4% |
| Experimental & laboratory | 59 | 0.67 | 0.74 | 0.70 | 17.8% |
| Dynamic & predictive modeling | 114 | 0.61 | 0.59 | 0.60 | 17.1% |
| Statistical & econometric | 55 | 0.53 | 0.24 | 0.33 | 9.3% |
| Policy & LDN framework | 11 | 0.00 | 0.00 | 0.00 | 1.0% |
| Total / weighted | **503** | 0.64 acc. | | 0.62 | 100% |

**Answer to Reviewer 1 ("did you ever validate the model you used?"):** the corpus shares come from the 20-class MLP
(+ manual review), not from the family model. D. An independent prediction of all 2,151 articles by the family
model agrees with the paper's family labels for **71.3%** of articles (κ = 0.63), and the **family shares agree within
2.4 points** (paper vs family model: qualitative 30.5 vs 32.9; geospatial 24.4 vs 25.8; experimental 17.8 vs 17.2;
dynamic 17.1 vs 16.7; statistical 9.3 vs 7.3; LDN 1.0 vs 0.1). So family-level shares are robust to which classifier
is used; the 20-class percentages are not reliable and should be reported only descriptively (or in the Supplement).

## Reviewer 2 (iv) — confidence threshold → `02` (B) and `03_confidence_band_audit.xlsx`

- Low band (< 0.5): **242 records, all manually reviewed; 135 relabelled (102 to a different family); 107 confirmed.**
- Cross-validated accuracy by confidence band (MLP, held-out):

| Band | 20-class accuracy | Family accuracy |
|---|---|---|
| < 0.5 | 0.24 | 0.46 |
| 0.5–0.7 | 0.30 | 0.52 |
| 0.7–0.9 | 0.42 | 0.63 |
| ≥ 0.9 | 0.66 | 0.77 |

- Manual spot-check of predictions kept automatically (random, seed 2026, excluding the 503 reference abstracts;
  first-pass coding by Claude, 8 borderline cases flagged `[AMBIGUOUS]` for author verification):

| Band | 20-class correct | Family correct |
|---|---|---|
| Medium (0.5–0.9), n = 20 | 9 (45%) | 13 (65%) |
| High (≥ 0.9), n = 20 | 12 (60%) | 16 (80%) |

**Take-away:** the spot-check matches the cross-validated calibration. Confidence is informative (accuracy rises
with confidence) but not a guarantee — another reason to rest conclusions on family-level shares, which are robust
(see D above), rather than on individual labels or fine-grained percentages.

## Reviewer 2 (v) — affiliation vs study location → `06_geography.py`

Affiliation countries re-extracted from Scopus for exactly the 2,151 articles (2,097 with ≥ 1 resolvable country);
study-location countries extracted from title + abstract with a country/demonym/sub-national gazetteer
(copyright lines removed). Location found for **1,597 articles (74.2%)**; manual check of 30 random articles:
**primary study country correct in 30/30**, 2 also listed an incidental comparison country.

| Sub-region | Share of affiliations | Share of study locations | Studies with ≥ 1 author in that sub-region |
|---|---|---|---|
| Eastern Asia | 24.3% | 23.0% | 91% |
| Western Europe | 16.8% | **0.9%** | – |
| Northern America | 14.9% | **3.8%** | 72% |
| Southern Europe | 13.8% | 9.3% | 90% |
| Southern Asia | 12.2% | 12.9% | 89% |
| Northern Europe | 12.1% | **0.8%** | – |
| Eastern Africa | 8.2% | **13.7%** | **69%** |
| South America | 6.7% | 7.2% | 85% |
| Northern Africa | 3.6% | 4.3% | 74% |
| Western Africa | 3.5% | 5.0% | **62%** |
| Central America | 1.5% | 1.9% | 66% |

**Take-away:** Western and Northern Europe and Northern America produce ~44% of the research but host < 6% of study sites; African
sub-regions are studied more than their institutions publish, and roughly a third of studies located in Eastern
and Western Africa have no locally affiliated author. This (a) confirms the reviewer's point, (b) shows that the
manuscript's statement that Northern Africa "contributes" 1% concerns *production*, not *attention*, and (c) turns the
geography section into a stronger, two-sided finding: research attention is broadly distributed, research
*production* is concentrated, and local authorship is lowest where degradation burdens are high.

Country counts: the manuscript's numbers (USA 371, India 255, UK 213 …) come from Scopus's *Analyze results* run on
the full combined query with **all document types**; on the 2,151-article corpus they are China 459, USA 290, UK 167,
Germany 160, India 154, Italy 154, Australia 127, Spain 102, Netherlands 86, South Africa 85, Ethiopia 84, Brazil 78.

## Thematic counts and Figure 4 → `04_themes_by_year.py`, `outputs/Figure_4_revised.tif`

- Old Figure 4 and the "67% (2012) → 77% (2024)" statement came from a **third dataset** (ArcGIS dashboard export of
  19 Jan 2026, 2,957 query hits, more 2025 records than the corpus). Rebuilt on the 2,151 corpus (multi-label, ≤ 2024):
  impact studies were **67–86% of articles in every year 2010–2024 (mean 77%)**; 2012 = 66.7%, 2024 = 84.5%.
  The "steadily rising" wording is not supported; "consistently two-thirds or more" is.
- Overall shares: multi-label 78.3 / 21.5 / 5.5 / 0.7 % (impact / process / driver / feedback; 129 articles in > 1 dimension);
  single-assignment (as in manuscript) 76.8 / 17.2 / 5.3 / 0.7 %. Recommend reporting the multi-label figures and
  stating that the manuscript's de-duplication kept the first query's dimension.

## Sample sizes — one basis for each number (Reviewer 2 "inconsistent sample sizes")

| Number | What it is | Used for |
|---|---|---|
| 2,699 | records pooled from the 11 queries (all doc types) | PRISMA identification |
| 2,472 | Articles + Conference papers | classification input |
| 2,151 | after title de-duplication | **all reported shares, Figure 4 (revised), geography (revised)** |
| 503 | manually labelled reference abstracts (490 unique titles) | training/validation |
| 242 / 135 / 107 | low-confidence reviewed / relabelled / confirmed | Section 3.3.10 |
| 1,830 | unique WoS records | database sensitivity |

Still on a different basis unless re-run: **funding (Figure 6)** — Scopus *Analyze* on the combined query
(Feb 2025, all doc types). Either state that basis explicitly in the caption/text, or re-export funding for the 2,151 EIDs
(needs institutional/VPN access to full Scopus records).

## Smaller corrections found
- "Fewer than 5%" for scenario + coupled human–natural + systems/network: actual **23 articles (1.1%)**; with machine learning 95 (4.4%).
- RUSLE "63 articles": abstracts mentioning RUSLE or the Universal Soil Loss Equation = **60**, of which **37** also mention land use/land cover.
- Manuscript cites "Section 9" for limitations ≥ 7 times; no Limitations section exists (restore it).
- 19 cited works missing from the reference list (Mendeley refresh).
