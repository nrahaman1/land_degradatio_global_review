# Global Land Degradation Research Metadata

This repository includes the data and analysis scripts for the review.

Access ArcGIS Dashboard: https://www.arcgis.com/apps/dashboards/af9edd80847143beb9fb5e891985129f

## Revision 1 analyses (`revision1/`)

Validation and sensitivity analyses added in response to peer review (Discover Applied Sciences, October 2026). `revision1/RESULTS_SUMMARY.md` lists every result; outputs are in `revision1/outputs/`.

| Script | Analysis |
|---|---|
| `01_wos_scopus_overlap.py` | Web of Science replication of the Table 1 queries; overlap with the Scopus corpus |
| `02_classifier_validation.py` | Title-grouped cross-validation, calibration by confidence band, classifier-independence of family shares |
| `03_confidence_band_sample.py` | Random sample of medium- and high-confidence predictions for manual checking |
| `04_themes_by_year.py` | Thematic shares and Figure 4 on the 2,151-article corpus |
| `05_expanded_queries.py` | Original vs synonym-expanded Scopus queries |
| `06_geography.py` | Author affiliation vs study location by sub-region |

Requirements: pandas, numpy, scikit-learn, sentence-transformers, pycountry, requests, matplotlib. Scripts 01, 05 and 06 query the Scopus Search API and need a key in the `SCOPUS_API_KEY` environment variable. Script 01 also needs Web of Science exports in `revision1/WoS_Data/Qxx_*/` (search strings in `revision1/WoS_queries.txt`); these are not redistributed under Clarivate's terms. Run 01 before 02.
