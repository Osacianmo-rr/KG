import pandas as pd
from pathlib import Path

EXTERNAL_DIR = Path(__file__).resolve().parents[1] / "data" / "external"

# 读取 Excel
df_herb_comp = pd.read_excel(EXTERNAL_DIR / "23_Herbs_Molecules_Relationships.xlsx", engine='openpyxl')
df_comp_target = pd.read_excel(EXTERNAL_DIR / "34_Molecules_Targets_Relationships.xlsx", engine='openpyxl')

# 保存为 CSV
df_herb_comp.to_csv(EXTERNAL_DIR / "tcmsp_herb_ingredient.csv", index=False)
df_comp_target.to_csv(EXTERNAL_DIR / "tcmsp_ingredient_target.csv", index=False)

print(f"草药-成分: {len(df_herb_comp)} 条")
print(f"成分-靶点: {len(df_comp_target)} 条")