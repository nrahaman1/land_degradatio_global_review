"""Reviewer 2, comment (v): author affiliation (where research is produced) vs study location (where it is done).

1. Affiliation countries for exactly the 2,151-article corpus, from Scopus metadata (by EID); an article is
   counted once for every country/sub-region represented among its authors' affiliations.
2. Study-location countries extracted from title + abstract with a gazetteer of country
   names, demonyms and major sub-national units (longest match wins; known false friends are masked).
3. Sub-region comparison (UN M49 sub-regions as in Figure 5) and the share of studies located in a
   sub-region that have at least one author affiliated there.
Outputs: outputs/06_*.csv and outputs/06_location_precision_sample.csv (for manual checking).
"""
import json, os, re
import pandas as pd
import pycountry
from common import load_corpus, scopus_search, OUT, REPO

# ---------------------------------------------------------------- reference: country -> sub-region
geo = json.load(open(os.path.join(REPO, "data", "countries.geojson"), encoding="utf-8"))
SUBREGION = {f["properties"]["NAME_EN"]: f["properties"]["SUBREGION"] for f in geo["features"]}
CANON = {  # Scopus / pycountry spellings -> Natural Earth NAME_EN
    "Russian Federation": "Russia", "Viet Nam": "Vietnam", "Korea, Republic of": "South Korea",
    "Iran, Islamic Republic of": "Iran", "Syrian Arab Republic": "Syria", "Czechia": "Czech Republic",
    "Tanzania, United Republic of": "Tanzania", "Bolivia, Plurinational State of": "Bolivia",
    "Venezuela, Bolivarian Republic of": "Venezuela", "Lao People's Democratic Republic": "Laos",
    "Moldova, Republic of": "Moldova", "Türkiye": "Turkey", "Turkiye": "Turkey", "Cabo Verde": "Cape Verde",
    "Congo, The Democratic Republic of the": "Democratic Republic of the Congo",
    "Democratic Republic Congo": "Democratic Republic of the Congo", "Congo": "Republic of the Congo",
    "Côte d'Ivoire": "Ivory Coast", "Cote d'Ivoire": "Ivory Coast", "Eswatini": "Eswatini", "Swaziland": "Eswatini",
    "North Macedonia": "North Macedonia", "Macedonia": "North Macedonia", "Hong Kong": "China", "Macao": "China",
    "Taiwan, Province of China": "Taiwan", "Brunei Darussalam": "Brunei", "Palestine, State of": "Palestine",
    "Libyan Arab Jamahiriya": "Libya", "Micronesia, Federated States of": "Federated States of Micronesia",
    "Timor-Leste": "East Timor", "Serbia and Montenegro": "Serbia", "Bahamas": "The Bahamas", "Gambia": "The Gambia",
    "Myanmar": "Myanmar", "Burma": "Myanmar", "Korea, Democratic People's Republic of": "North Korea",
}


def canon(name):
    name = CANON.get(name, name)
    if name in SUBREGION:
        return name
    try:
        c = pycountry.countries.lookup(name)
        for n in (getattr(c, "common_name", None), c.name, getattr(c, "official_name", None)):
            n = CANON.get(n, n)
            if n in SUBREGION:
                return n
    except LookupError:
        pass
    return None


# ---------------------------------------------------------------- gazetteer for study locations
ALIASES = {
    "United States of America": ["united states", "usa", "u.s.a.", "u.s.", "conterminous us", "american southwest",
                                 "great plains", "mojave", "chihuahuan desert", "appalachia"] +
        ["alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida",
         "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
         "massachusetts", "michigan", "minnesota", "mississippi state", "missouri", "montana", "nebraska", "nevada",
         "new hampshire", "new jersey", "new mexico", "new york state", "north carolina", "north dakota", "ohio",
         "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota", "tennessee", "texas",
         "utah", "vermont", "virginia", "wisconsin", "wyoming"],
    "China": ["china", "chinese", "loess plateau", "tibetan plateau", "qinghai-tibet", "qinghai tibet", "inner mongolia",
              "mu us", "horqin", "ordos", "hunshandake", "three-river", "yangtze", "yellow river", "hexi corridor",
              "taklimakan", "tarim", "junggar", "karst region of southwest", "hong kong"] +
        ["anhui", "fujian", "gansu", "guangdong", "guangxi", "guizhou", "hainan", "hebei", "heilongjiang", "henan",
         "hubei", "hunan", "jiangsu", "jiangxi", "jilin", "liaoning", "ningxia", "qinghai", "shaanxi", "shandong",
         "shanxi", "sichuan", "xinjiang", "yunnan", "zhejiang", "beijing", "tianjin", "chongqing", "shanghai", "tibet"],
    "India": ["india", "indian", "rajasthan", "gujarat", "maharashtra", "karnataka", "tamil nadu", "kerala",
              "andhra pradesh", "telangana", "odisha", "orissa", "jharkhand", "chhattisgarh", "madhya pradesh",
              "uttar pradesh", "uttarakhand", "himachal pradesh", "punjab, india", "haryana", "bihar", "west bengal",
              "assam", "meghalaya", "sikkim", "jammu", "kashmir", "ladakh", "deccan", "thar desert", "western ghats"],
    "Australia": ["australia", "australian", "new south wales", "queensland", "victoria, australia", "tasmania",
                  "northern territory", "western australia", "murray-darling", "murray darling"],
    "Ethiopia": ["ethiopia", "ethiopian", "tigray", "amhara", "oromia", "blue nile"],
    "Brazil": ["brazil", "brazilian", "caatinga", "cerrado", "amazonia", "brazilian amazon"],
    "Spain": ["spain", "spanish", "andalusia", "murcia", "catalonia", "almeria", "canary islands", "valencia region"],
    "Italy": ["italy", "italian", "sicily", "sardinia", "basilicata", "apulia", "calabria", "tuscany", "campania"],
    "Iran": ["iran", "iranian", "persia"], "Kenya": ["kenya", "kenyan"], "Nigeria": ["nigeria", "nigerian", "niger delta"],
    "South Africa": ["south africa", "south african", "karoo", "kwazulu-natal", "eastern cape", "limpopo"],
    "Mexico": ["mexico", "mexican", "yucatan", "oaxaca"], "Mongolia": ["mongolia", "mongolian"],
    "Kazakhstan": ["kazakhstan", "kazakh"], "Russia": ["russia", "russian", "siberia"],
    "Morocco": ["morocco", "moroccan"], "Tunisia": ["tunisia", "tunisian"], "Egypt": ["egypt", "egyptian", "nile delta"],
    "Pakistan": ["pakistan", "pakistani"], "Bangladesh": ["bangladesh"], "Nepal": ["nepal", "nepalese"],
    "Turkey": ["turkey", "turkish", "anatolia"], "Argentina": ["argentina", "argentine", "patagonia"],
    "Chile": ["chile", "chilean"], "Peru": ["peru", "peruvian"], "Bolivia": ["bolivia", "bolivian"],
    "Uganda": ["uganda", "ugandan"], "United Republic of Tanzania": ["tanzania", "tanzanian"],
    "Ghana": ["ghana", "ghanaian"], "Burkina Faso": ["burkina faso", "burkinabe"], "Mali": ["mali"],
    "Senegal": ["senegal", "senegalese"], "Zimbabwe": ["zimbabwe", "zimbabwean"], "Namibia": ["namibia", "namibian"],
    "Botswana": ["botswana"], "Germany": ["germany", "german"], "France": ["france"], "Portugal": ["portugal", "portuguese"],
    "Greece": ["greece", "greek", "crete"], "Syria": ["syria", "syrian"], "Iraq": ["iraq", "iraqi"],
    "Saudi Arabia": ["saudi arabia", "saudi"], "Israel": ["israel", "israeli", "negev"], "Vietnam": ["vietnam", "viet nam", "vietnamese"],
    "Thailand": ["thailand", "thai"], "Indonesia": ["indonesia", "indonesian", "java", "sumatra", "borneo", "kalimantan"],
    "Malaysia": ["malaysia", "malaysian"], "Philippines": ["philippines", "philippine"], "Japan": ["japan", "japanese"],
    "South Korea": ["south korea", "korean"], "Sri Lanka": ["sri lanka", "sri lankan"], "Afghanistan": ["afghanistan", "afghan"],
    "Algeria": ["algeria", "algerian"], "Libya": ["libya", "libyan"], "Sudan": ["sudan", "sudanese"],
    "Somalia": ["somalia", "somali"], "Rwanda": ["rwanda", "rwandan"], "Malawi": ["malawi", "malawian"],
    "Zambia": ["zambia", "zambian"], "Mozambique": ["mozambique"], "Madagascar": ["madagascar", "malagasy"],
    "Cameroon": ["cameroon"], "Canada": ["canada", "canadian", "prairies of canada"], "Uzbekistan": ["uzbekistan", "uzbek"],
    "Tajikistan": ["tajikistan"], "Kyrgyzstan": ["kyrgyzstan", "kyrgyz"], "Turkmenistan": ["turkmenistan"],
    "Jordan": ["jordan, ", "kingdom of jordan", "jordanian"], "Ukraine": ["ukraine", "ukrainian"],
    "Poland": ["poland", "polish"], "Romania": ["romania", "romanian", "transylvania"], "Hungary": ["hungary", "hungarian"],
    "United Kingdom": ["united kingdom", "britain", "british", "england", "scotland", "wales", "northern ireland"],
    "Iceland": ["iceland", "icelandic"], "Niger": ["niger republic", "republic of niger"],
    "Democratic Republic of the Congo": ["democratic republic of the congo", "dr congo", "drc"],
}
# phrases that must not produce a match (masked before matching)
FALSE_FRIENDS = ["indian ocean", "indian summer monsoon", "indian monsoon", "american society", "french paradox",
                 "german research foundation", "british columbia", "new england", "niger river", "river niger",
                 "jordan river", "guinea pig", "turkey oak", "chinese fir", "chinese pine", "chinese tallow",
                 "chinese academy", "spanish broom", "mexican hat", "mali index", "georgia"]


def build_gazetteer():
    terms = {}
    for name in SUBREGION:
        terms[name.lower()] = name
    for c in pycountry.countries:
        n = canon(c.name)
        if n:
            for alias in {c.name, getattr(c, "common_name", c.name), getattr(c, "official_name", c.name)}:
                if len(alias) > 3:
                    terms[alias.lower()] = n
    for country, al in ALIASES.items():
        n = canon(country) or country
        for a in al:
            terms[a.lower()] = n
    for bad in ("georgia", "jordan", "chad", "niger", "guinea", "dominica"):  # ambiguous (US state, rivers, lakes...)
        terms.pop(bad, None)
    terms = {k: v for k, v in terms.items() if v in SUBREGION}
    pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(terms, key=len, reverse=True)) + r")\b")
    return terms, pattern


def study_countries(text, terms, pattern):
    # drop the publisher copyright line (e.g. "(c) 2020 ... Licensee MDPI, Basel, Switzerland")
    t = " " + re.split(r"©|\(c\)\s*\d{4}|copyright|published by", str(text).lower())[0] + " "
    for ff in FALSE_FRIENDS:
        t = t.replace(ff, " ")
    return sorted({terms[m] for m in pattern.findall(t)})


def main():
    a, u = load_corpus()

    # ---- 1. affiliation countries from Scopus (by EID, 25 per request)
    eids = u.eid.tolist(); aff = {}
    for i in range(0, len(eids), 25):
        q = " OR ".join(f"EID({e})" for e in eids[i:i + 25])
        for e in scopus_search(q, fields="eid,affiliation")[1]:
            aff[e["eid"]] = sorted({canon(x.get("affiliation-country") or "") for x in e.get("affiliation", [])} - {None})
    u["aff_countries"] = u.eid.map(lambda e: aff.get(e, []))
    print(f"affiliation metadata returned for {sum(e in aff for e in eids)} / {len(eids)} articles; "
          f"{(u.aff_countries.map(len) > 0).sum()} with >=1 resolvable country")

    # ---- 2. study-location countries
    terms, pattern = build_gazetteer()
    text = u.Title.fillna("") + ". " + u.Abstract.fillna("")  # corpus file has no author-keyword column
    u["study_countries"] = [study_countries(t, terms, pattern) for t in text]
    n_loc = (u.study_countries.map(len) > 0).sum()
    print(f"study location detected for {n_loc} / {len(u)} articles ({100 * n_loc / len(u):.1f}%); "
          f"{(u.study_countries.map(len) > 3).sum()} mention >3 countries (multi-country/global)")

    # ---- 3. comparisons
    sub = lambda cs: sorted({SUBREGION[c] for c in cs})
    u["aff_sub"] = u.aff_countries.map(sub); u["study_sub"] = u.study_countries.map(sub)

    def per(col):
        return u[col].explode().value_counts()
    countries = pd.DataFrame({"affiliation_articles": per("aff_countries"), "study_location_articles": per("study_countries")}).fillna(0).astype(int)
    countries["subregion"] = countries.index.map(SUBREGION)
    countries.sort_values("affiliation_articles", ascending=False).to_csv(f"{OUT}/06_countries_affiliation_vs_study.csv")

    subs = pd.DataFrame({"affiliation_articles": per("aff_sub"), "study_location_articles": per("study_sub")}).fillna(0).astype(int)
    subs["affiliation_share_%"] = (100 * subs.affiliation_articles / (u.aff_sub.map(len) > 0).sum()).round(1)
    subs["study_share_%"] = (100 * subs.study_location_articles / (u.study_sub.map(len) > 0).sum()).round(1)
    located = u[u.study_sub.map(len).between(1, 3)]  # single- or few-region studies
    subs["studies_with_local_author_%"] = pd.Series({
        s: round(100 * located[located.study_sub.map(lambda x: s in x)].apply(lambda r: s in r.aff_sub, axis=1).mean(), 1)
        for s in subs.index if (located.study_sub.map(lambda x: s in x)).sum() >= 10})
    subs = subs.sort_values("study_location_articles", ascending=False)
    subs.to_csv(f"{OUT}/06_subregions_affiliation_vs_study.csv")
    u[["eid", "Title", "aff_countries", "study_countries"]].to_csv(f"{OUT}/06_article_geography.csv", index=False)
    u[u.study_countries.map(len) > 0].sample(30, random_state=2026)[["eid", "Title", "study_countries"]].to_csv(
        f"{OUT}/06_location_precision_sample.csv", index=False)

    print("\nTop countries:\n", countries.sort_values("affiliation_articles", ascending=False).head(15).to_string())
    print("\nSub-regions:\n", subs.to_string())


if __name__ == "__main__":
    main()
