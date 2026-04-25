import os
import re
import pandas as pd

QS_RANKING_PATH = os.path.join(
    os.path.dirname(__file__), 
    "..", "..", "qs_rankings", 
    "2026 QS World University Rankings 1.3 (For qs.com).xlsx"
)

_QS_DF = None

def get_qs_ranking(uni_name: str) -> tuple[str, int | None]:
    if not uni_name:
        return uni_name, None
        
    global _QS_DF
    if _QS_DF is None:
        if not os.path.exists(QS_RANKING_PATH):
            return uni_name, None
        # The actual headers are on row 2 (index 2 in pandas when skipping row 0, 1)
        _QS_DF = pd.read_excel(QS_RANKING_PATH, header=2)
        
    if _QS_DF.empty:
        return uni_name, None
        
    def clean_name(name):
        if not isinstance(name, str): 
            return ""
        name = name.lower()
        # Remove special characters
        name = re.sub(r'[^a-z0-9]', '', name)
        return name
        
    search_str = clean_name(uni_name)
    if not search_str:
        return uni_name, None
        
    if 'Name' not in _QS_DF.columns or 'Rank' not in _QS_DF.columns:
        return uni_name, None
        
    for _, row in _QS_DF.iterrows():
        row_name = row['Name']
        if not isinstance(row_name, str): 
            continue
            
        c_row_name = clean_name(row_name)
        if search_str == c_row_name or (search_str in c_row_name and len(search_str) > 10) or (c_row_name in search_str and len(c_row_name) > 10):
            rank_val = row['Rank']
            if isinstance(rank_val, str):
                nums = re.findall(r'\d+', rank_val)
                if nums:
                    return row_name, int(nums[0])
            elif isinstance(rank_val, (int, float)):
                return row_name, int(rank_val)
                
    return uni_name, None
