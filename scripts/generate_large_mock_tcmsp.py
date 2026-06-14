# scripts/generate_large_mock_tcmsp.py
import random
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DICT_DIR = PROJECT_ROOT / "data" / "dictionaries"
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"
EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

# 读取 herb.txt
herb_file = DICT_DIR / "herb.txt"
with open(herb_file, 'r', encoding='utf-8') as f:
    herbs = [line.strip() for line in f if line.strip()]

random.seed(42)
all_hi = []
all_it = []

for herb in herbs:
    num_ing = random.randint(50, 100)
    for _ in range(num_ing):
        ing = f"ING_{herb.replace(' ', '_')}_{random.randint(100000, 999999)}"
        all_hi.append((herb, ing))
        num_tar = random.randint(30, 60)
        for __ in range(num_tar):
            tar = f"TAR_{random.randint(1000000, 9999999)}"
            all_it.append((ing, tar))

df_hi = pd.DataFrame(all_hi, columns=['herb', 'ingredient'])
df_it = pd.DataFrame(all_it, columns=['ingredient', 'target'])
df_hi.to_csv(EXTERNAL_DIR / "mock_herb_ingredient.csv", index=False)
df_it.to_csv(EXTERNAL_DIR / "mock_ingredient_target.csv", index=False)

print(f"生成 herb->ingredient: {len(df_hi)} 条")
print(f"生成 ingredient->target: {len(df_it)} 条")
print(f"成分节点数（去重）: {df_hi['ingredient'].nunique()}")
print(f"靶点节点数（去重）: {df_it['target'].nunique()}")