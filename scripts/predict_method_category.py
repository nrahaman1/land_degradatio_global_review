

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, r2_score
from sklearn.preprocessing import LabelEncoder
import logging
import os
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = r"C:\Users\nafiz\OneDrive - Mississippi State University\NSF_MSU_Project_Shared\Review_Paper\CSV\Abstract_and_data_core_insights"
INPUT_FILE = os.path.join(BASE_DIR, "Consolidated_Method_Extraction_Enhanced_Excel_Automated_Only_Article.xlsx")
OUTPUT_FILE = os.path.join(BASE_DIR, "Consolidated_Method_Prediction.csv")

def predict_methods():
    logging.info("Loading Data...")
    try:
        xl = pd.ExcelFile(INPUT_FILE)
        df = xl.parse(xl.sheet_names[0])
    except Exception as e:
        logging.error(f"Failed to load Excel: {e}")
        return

    if 'Method_Category_Manual' not in df.columns or 'Abstract' not in df.columns:
        logging.error("Required columns missing.")
        return
        
    train_df = df[df['Method_Category_Manual'].notna()]
    
    logging.info(f"Total Rows: {len(df)}")
    logging.info(f"Labeled Training Examples: {len(train_df)}")
    
    if len(train_df) < 10:
        logging.error("Not enough labeled data.")
        return

    # 1. Embeddings
    logging.info("Generating Embeddings for ALL abstracts...")
    model = SentenceTransformer('all-MiniLM-L6-v2') 
    
    df['Abstract'] = df['Abstract'].fillna("")
    abstracts = df['Abstract'].astype(str).tolist()
    embeddings = model.encode(abstracts, show_progress_bar=True)
    
    # Filter out classes with only 1 sample for stratified split
    class_counts = train_df['Method_Category_Manual'].value_counts()
    valid_classes = class_counts[class_counts >= 2].index
    
    # We only use rows with valid classes for the Validation Split
    train_df_val = train_df[train_df['Method_Category_Manual'].isin(valid_classes)]
    
    logging.info(f"Filtered Training Examples (Count >= 2): {len(train_df_val)} (Original: {len(train_df)})")
    
    # Update indices and labels for validation part
    train_indices = train_df_val.index
    X_labeled = embeddings[train_indices]
    y_labels = train_df_val['Method_Category_Manual'].values
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y_labels)
    classes = le.classes_
    logging.info(f"Classes: {classes}")

    # 3. 50% Split Validation
    logging.info("Performing 50/50 Split Validation...")
    X_train, X_test, y_train, y_test = train_test_split(X_labeled, y_encoded, test_size=0.5, random_state=42, stratify=y_encoded)
    
    # Deep Learning Model (MLP)
    # 2 Hidden Layers (128, 64)
    clf = MLPClassifier(hidden_layer_sizes=(128, 64), activation='relu', solver='adam', alpha=0.0001, 
                        batch_size='auto', learning_rate='adaptive', learning_rate_init=0.001, 
                        max_iter=1000, random_state=42)
    
    clf.fit(X_train, y_train)
    y_pred_val = clf.predict(X_test)
    
    val_acc = accuracy_score(y_test, y_pred_val)
    # Calculate R2 (Note: R2 is not standard for classification, but evaluating per request)
    val_r2 = r2_score(y_test, y_pred_val)
    
    logging.info("----- Validation Results (50% Split) -----")
    logging.info(f"Accuracy: {val_acc:.4f}")
    logging.info(f"R2 Score: {val_r2:.4f}")
    logging.info(f"Classification Report:\n{classification_report(y_test, y_pred_val, target_names=classes)}")
    
    # 4. Final Training on All Labeled Data (Including rare classes)
    logging.info("Retraining on ALL labeled data (including singletons) for final predictions...")
    
    # For final model, we use the FULL train_df, not just filtered
    train_indices_full = train_df.index
    X_labeled_full = embeddings[train_indices_full]
    y_labels_full = train_df['Method_Category_Manual'].values
    
    # Re-encode with full set of classes
    le_full = LabelEncoder()
    y_encoded_full = le_full.fit_transform(y_labels_full)
    
    # Re-init model
    clf_final = MLPClassifier(hidden_layer_sizes=(128, 64), activation='relu', solver='adam', alpha=0.0001, 
                              max_iter=1000, random_state=42)
    clf_final.fit(X_labeled_full, y_encoded_full)
    
    # 5. Predict on ALL
    predictions_encoded = clf_final.predict(embeddings)
    probabilities = clf_final.predict_proba(embeddings)
    confidence_scores = np.max(probabilities, axis=1)
    
    predictions_labels = le_full.inverse_transform(predictions_encoded)
    
    df['Predicted_Method_Category'] = predictions_labels
    df['Prediction_Confidence'] = np.round(confidence_scores, 4)
    
    logging.info(f"Saving results to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)
    logging.info("Done.")

if __name__ == "__main__":
    predict_methods()
