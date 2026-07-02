
import pandas as pd
from transformers import pipeline
import os
from tqdm import tqdm
import logging
import torch

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Base directory containing all the subfolders
BASE_DIR = r"C:\Users\nafiz\OneDrive - Mississippi State University\NSF_MSU_Project_Shared\Review_Paper\CSV\Abstract_and_data_core_insights"

# Initialize QA Pipeline once
logging.info("Initializing BERT/RoBERTa model...")
model_name = "deepset/roberta-base-squad2"
try:
    # Check for GPU
    device = 0 if torch.cuda.is_available() else -1
    qa_pipeline = pipeline('question-answering', model=model_name, tokenizer=model_name, device=device)
    logging.info(f"Model loaded successfully on device {'GPU' if device==0 else 'CPU'}.")
except Exception as e:
    logging.error(f"Failed to load model: {e}")
    exit(1)

def process_folder(folder_path):
    folder_name = os.path.basename(folder_path)
    # Try 'Abstract.csv' first (User correction), then 'Abstracts.csv'
    csv_candidates = ["Abstract.csv", "Abstracts.csv"]
    csv_path = None
    for candidate in csv_candidates:
        candidate_path = os.path.join(folder_path, candidate)
        if os.path.exists(candidate_path):
            csv_path = candidate_path
            break
    
    if not csv_path:
        logging.warning(f"Skipping {folder_name}: Abstract.csv (or Abstracts.csv) not found.")
        return

    logging.info(f"Processing folder: {folder_name} using {os.path.basename(csv_path)}")
    
    try:
        df = pd.read_csv(csv_path)
        if 'Abstract' not in df.columns:
            logging.error(f"Skipping {folder_name}: 'Abstract' column missing.")
            return
            
        # Drop empty abstracts
        df = df.dropna(subset=['Abstract'])
        
        results = []
        question = "What research method, model, or analysis technique is used?"
        
        # Batch inference could be faster but iterating is safer for error handling per row
        for index, row in tqdm(df.iterrows(), total=len(df), desc=f"Extracting {folder_name[:20]}"):
            abstract_text = row['Abstract']
            try:
                res = qa_pipeline({
                    'question': question,
                    'context': abstract_text
                })
                
                results.append({
                    'Original_Row_Index': index,
                    'Abstract_Snippet': str(abstract_text)[:100] + "...",
                    'Extracted_Method': res['answer'],
                    'Confidence_Score': res['score']
                })
            except Exception as e:
                # logging.debug(f"Error on row {index} in {folder_name}: {e}")
                continue
                
        # Save results
        if results:
            results_df = pd.DataFrame(results)
            # Remove "AND" from folder name for the output file
            # Replace " AND " with space, then clean up double spaces if any
            clean_name = folder_name.replace(" AND ", " ").replace("  ", " ").strip()
            output_filename = f"NLP_Extracted_Methods_{clean_name}.csv"
            output_path = os.path.join(folder_path, output_filename)
            results_df.to_csv(output_path, index=False)
            logging.info(f"Saved {len(results_df)} records to {output_filename}")
        else:
            logging.warning(f"No results extracted for {folder_name}")

    except Exception as e:
        logging.error(f"Critical error processing {folder_name}: {e}")

def main():
    # List all subdirectories
    try:
        subfolders = [f.path for f in os.scandir(BASE_DIR) if f.is_dir()]
    except FileNotFoundError:
        logging.error(f"Base Directory not found: {BASE_DIR}")
        exit(1)
        
    logging.info(f"Found {len(subfolders)} subdirectories.")
    
    for folder in subfolders:
        process_folder(folder)

    logging.info("Batch processing complete.")

if __name__ == "__main__":
    main()
