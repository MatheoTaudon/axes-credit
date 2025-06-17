import os
import pandas as pd
from datetime import datetime

def load_latest_excel():
    today = datetime.today().strftime("%Y%m%d")
    file_name = f"Axes_{today}.xlsx"
    file_path = os.path.join("data", file_name)
    
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        return df
    else:
        return None