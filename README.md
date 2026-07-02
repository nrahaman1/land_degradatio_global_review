# Global Land Degradation Research Metadata

This repository includes the data and analysis code for the review article
*"Geographic, thematic, and methodological asymmetries in land degradation science: the case for a more anticipatory research agenda."*

**Interactive ArcGIS Dashboard:** https://www.arcgis.com/apps/dashboards/af9edd80847143beb9fb5e891985129f

## Data (`/data`)

- `Consolidated_Method_Prediction_Excel_Updated.xlsx` — classified corpus, including the manually labelled reference set (`Method_Category_Manual`), the RoBERTa-extracted method/model/technique spans, the predicted method category, and the confidence score.
- `All_Years_Merged.csv` — annual counts of studies by thematic dimension (drivers, processes, impacts, feedback).
- `Scopus-10-Analyze-FundingSponsor.csv` — funding organizations/countries supporting the research.
- `countries.geojson`, `subregions.geojson` — spatial boundaries with research-metadata scores.

> Country counts come from Scopus's **Country/Territory** analysis, i.e. by the **authors' institutional affiliations** (research output/origin); they are distinct from where degradation occurs or is studied.

## Analysis scripts (`/scripts`)

| Script | Pipeline stage |
|--------|----------------|
| `scopus_search.py` | Record retrieval via the Scopus Search/Abstract APIs. **Insert your own Scopus API key** (the original key has been redacted). |
| `batch_nlp_extraction.py` | RoBERTa-base question-answering extraction of the research method, model, and analysis technique from each abstract. |
| `predict_method_category.py` | Sentence-BERT embedding + MLP classifier assigning each abstract to one of 20 methodological classes. |
| `revalidate_method_families.py` | Collapses the 20 classes into six coarse method families and reports cross-validated performance (accuracy, macro/weighted F1, Cohen's κ, confusion matrix) — reproduces Section 3.3.11. Self-contained against `/data`. |
| `remove_duplicates.py` | Title-based de-duplication of the corpus. |
| `add_funding_country.py` | Maps funding organizations to countries. |
| `aggregate_results.py` | Aggregates predictions into the thematic/method summaries used in the figures. |

### Reproducing the validation
```bash
pip install pandas numpy scikit-learn sentence-transformers openpyxl
python scripts/revalidate_method_families.py
```
This cross-validates the six-family classifier on the labelled reference set in `data/Consolidated_Method_Prediction_Excel_Updated.xlsx` and prints the metrics reported in the paper. The other scripts reference the authors' local corpus paths and are provided for transparency; adjust paths before running.

---
*Mississippi State University — NSF HEGS Project #2343014.*
