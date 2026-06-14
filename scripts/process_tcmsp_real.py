import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TCMSP_DIR = PROJECT_ROOT / "data" / "tcmsp"
TCMSP_DIR.mkdir(parents=True, exist_ok=True)

# 假设你已将下载的 Excel 文件放在 data/tcmsp/ 目录下
herb_comp_file = TCMSP_DIR / "23_Herbs_Molecules_Relationships.xlsx"
comp_target_file = TCMSP_DIR / "34_Molecules_Targets_Relationships.xlsx"

df_hc = pd.read_excel(herb_comp_file, engine='openpyxl')
df_ct = pd.read_excel(comp_target_file, engine='openpyxl')

print(f"草药-成分关系数: {len(df_hc)}")
print(f"成分-靶点关系数: {len(df_ct)}")

# 提取节点
herbs = set(df_hc['herb_id'])
ingredients = set(df_hc['molecule_id']).union(set(df_ct['molecule_id']))
targets = set(df_ct['target_id'])

nodes = []
for h in herbs:
    nodes.append({'id': h, 'type': 'Herb', 'name': h})
for i in ingredients:
    nodes.append({'id': i, 'type': 'Ingredient', 'name': i})
for t in targets:
    nodes.append({'id': t, 'type': 'Target', 'name': t})

# 生成关系
rels = []
for _, row in df_hc.iterrows():
    rels.append({
        'source': row['herb_id'],
        'source_type': 'Herb',
        'target': row['molecule_id'],
        'target_type': 'Ingredient',
        'relation': 'CONTAINS_INGREDIENT'
    })
for _, row in df_ct.iterrows():
    rels.append({
        'source': row['molecule_id'],
        'source_type': 'Ingredient',
        'target': row['target_id'],
        'target_type': 'Target',
        'relation': 'ACTS_ON'
    })

# 保存到 external 目录（供合并脚本使用）
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"
EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

pd.DataFrame(nodes).to_csv(EXTERNAL_DIR / "tcmsp_nodes.csv", index=False, encoding='utf-8-sig')
pd.DataFrame(rels).to_csv(EXTERNAL_DIR / "tcmsp_rels.csv", index=False, encoding='utf-8-sig')

print(f"TCMSP 节点数: {len(nodes)}")
print(f"TCMSP 关系数: {len(rels)}")