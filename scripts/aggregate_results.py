
import pandas as pd
import os
import glob
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = r"C:\Users\nafiz\OneDrive - Mississippi State University\NSF_MSU_Project_Shared\Review_Paper\CSV\Abstract_and_data_core_insights"
OUTPUT_FILE = os.path.join(BASE_DIR, "Consolidated_Method_Extraction_Enhanced.csv")

def aggregate_data():
    all_data = []
    
    # List all subdirectories
    try:
        subfolders = [f.path for f in os.scandir(BASE_DIR) if f.is_dir()]
    except FileNotFoundError:
        logging.error(f"Base Directory not found: {BASE_DIR}")
        exit(1)
        
    logging.info(f"Found {len(subfolders)} subdirectories. Starting enhanced aggregation...")
    
    for folder_path in subfolders:
        folder_name = os.path.basename(folder_path)
        
        # Exclude 'All' folder
        if folder_name.lower() == "all":
            logging.info("Skipping 'All' folder during aggregation.")
            continue
            
        # Find Enhanced Results CSV
        # We look for the pattern Enhanced_NLP_Methods_*.csv
        result_files = glob.glob(os.path.join(folder_path, "Enhanced_NLP_Methods_*.csv"))
        if not result_files:
            logging.warning(f"Skipping {folder_name}: No Enhanced NLP results found.")
            continue
        
        # Take the most recent one
        result_csv_path = result_files[0]
        
        try:
            # Load DataFrame
            df = pd.read_csv(result_csv_path)
            
            # Use columns as is, maybe verify Source_Folder is present? 
            # The enhanced script adds it. But let's overwrite/ensure it matches the folder name just in case.
            # (Clean name from folder)
            clean_name = folder_name.replace(" AND ", " ").replace("  ", " ").strip()
            df['Source_Folder'] = clean_name
            
            all_data.append(df)
            logging.info(f"Loaded {len(df)} records from {folder_name}")
            
        except Exception as e:
            logging.error(f"Error loading data for {folder_name}: {e}")
            continue

    # Concatenate all
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(OUTPUT_FILE, index=False)
        logging.info(f"Successfully created consolidated CSV with {len(final_df)} rows.")
        logging.info(f"Saved to: {OUTPUT_FILE}")
    else:
        logging.warning("No data was aggregated.")

if __name__ == "__main__":
    aggregate_data()
