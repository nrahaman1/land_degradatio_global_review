
import pandas as pd
import os

FILE_PATH = r"C:\Users\nafiz\OneDrive - Mississippi State University\NSF_MSU_Project_Shared\Review_Paper\CSV\Abstract_and_data_core_insights\Consolidated_Method_Prediction_Excel_Updated_CSV.csv"

def clean_data():
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        # Try finding it in the directory just in case path string has issues
        return

    try:
        # Try reading with default encoding, if fail, try latin1/cp1252
        try:
            df = pd.read_csv(FILE_PATH)
        except UnicodeDecodeError:
            df = pd.read_csv(FILE_PATH, encoding='latin1')
            
        print(f"Original Row Count: {len(df)}")
        
        # Check if 'Title' exists
        title_col = 'Title'
        if 'Title' not in df.columns:
            # Case insensitive check
            cols_lower = {c.lower(): c for c in df.columns}
            if 'title' in cols_lower:
                title_col = cols_lower['title']
                print(f"Using column '{title_col}' for Title.")
            else:
                print("Error: 'Title' column not found.")
                # print first few columns to debug
                print(f"Columns found: {df.columns.tolist()[:10]}...")
                return

        # Canonicalize title for better duplicate detection? (strip whitespace, lower case?)
        # User just said "based on the title column", strictly speaking that implies exact match.
        # But usually titles might have slight space variations. 
        # I'll stick to exact match unless I see issues, or maybe just strip whitespace.
        
        # Let's clean the column temporarily for checking? No, drop_duplicates is best on raw or slightly stripped.
        # I will just use drop_duplicates on the column as is, maybe strip whitespace.
        
        # Actually, let's just strip whitespace from the Title column to be safe, but modifying the column might generally be desired.
        # I'll do standard drop_duplicates.
        
        df_cleaned = df.drop_duplicates(subset=[title_col], keep='first')
        
        print(f"Cleaned Row Count: {len(df_cleaned)}")
        removed_count = len(df) - len(df_cleaned)
        print(f"Removed {removed_count} duplicates.")
        
        if removed_count > 0:
            df_cleaned.to_csv(FILE_PATH, index=False)
            print(f"Saved cleaned data to {FILE_PATH}")
        else:
            print("No duplicates found. File unchanged.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_data()
