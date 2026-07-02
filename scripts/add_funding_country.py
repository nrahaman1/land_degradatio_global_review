
import pandas as pd
import pycountry
from transformers import pipeline
import logging
import os
import re

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = r"C:\Users\nafiz\OneDrive - Mississippi State University\NSF_MSU_Project_Shared\Review_Paper\CSV\Abstract_and_data_core_insights"
INPUT_FILE = os.path.join(BASE_DIR, "Scopus-10-Analyze-FundingSponsor.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "Scopus-10-Analyze-FundingSponsor_With_Country.csv")

# Initialize NLP Pipeline for tough cases
# usage: fill_mask("The [Org] is located in [MASK].")
try:
    nlp = pipeline("fill-mask", model="bert-base-uncased")
except Exception as e:
    logging.warning(f"Could not load NLP model: {e}. Will rely on heuristics.")
    nlp = None

def get_country_from_text(text):
    if not isinstance(text, str):
        return "Unknown"
    
    # 1. Direct Lookup (Pycountry)
    # Check if any country name appears in the text
    for country in pycountry.countries:
        if country.name.lower() in text.lower():
            return country.name
    
    # Check common acronyms/substrings manually
    text_lower = text.lower()
    if "usa" in text_lower or "u.s." in text_lower or "national science foundation" in text_lower or "nsf" in text_lower:
        return "United States"
    if "uk" in text_lower or "united kingdom" in text_lower:
        return "United Kingdom"
    if "eu" in text_lower or "european" in text_lower or "horizon 2020" in text_lower:
        return "European Union"
    if "capes" in text_lower or "cnpq" in text_lower:
        return "Brazil"
    if "conacyt" in text_lower:
        return "Mexico"
        
    return None

def predict_country_nlp(org_name):
    if not nlp:
        return "Unknown"
        
    try:
        # Prompt engineering for BERT
        prompt = f"{org_name} is a funding agency located in [MASK]."
        res = nlp(prompt)
        # res is a list of dicts. We take the top prediction token_str
        # Check top 5 for a country name
        for r in res:
            token = r['token_str'].strip().title()
            # Verify if it's a valid country
            try:
                if pycountry.countries.lookup(token):
                    return token
            except:
                pass
                
        # Second attempt with different prompt
        prompt = f"{org_name} is based in [MASK]."
        res = nlp(prompt)
        for r in res:
            token = r['token_str'].strip().title()
            try:
                if pycountry.countries.lookup(token):
                    return token
            except:
                pass
                
    except Exception as e:
        # logging.debug(f"NLP failed for {org_name}: {e}")
        pass
        
    return "Unknown"

def main():
    if not os.path.exists(INPUT_FILE):
        logging.error(f"Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    logging.info(f"Loaded {len(df)} rows.")

    countries = []
    
    for index, row in df.iterrows():
        org = row.iloc[0] # Assuming first col is Name
        
        # 1. Heuristic
        country = get_country_from_text(org)
        
        # 2. NLP
        if not country:
            country = predict_country_nlp(org)
            
        countries.append(country)
        logging.info(f"Processed: {org[:30]}... -> {country}")

    df['Country'] = countries
    
    df.to_csv(OUTPUT_FILE, index=False)
    logging.info(f"Result saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
