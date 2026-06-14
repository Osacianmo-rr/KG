#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
处理 Dryad 数据库中的中药-成分-靶点数据，并引入症状、功效、草药配伍关系
生成节点和关系文件，草药节点仅保留有拉丁名的条目。
"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "tcmsp"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_with_fallback(file_path):
    """尝试多种编码读取 CSV 文件，并清理列名中的首尾空格"""
    encodings = ['utf-8-sig', 'gbk', 'gb2312', 'latin1', 'cp1252', 'utf-8']
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            # 关键：去除列名中的首尾空格
            df.columns = df.columns.str.strip()
            print(f"成功读取 {file_path.name}，编码: {enc}")
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise UnicodeDecodeError(f"无法解码文件 {file_path}，请检查文件编码。")


# ==================== 1. 读取原始文件 ====================
df_hc = read_csv_with_fallback(DATA_DIR / "herb_compound.csv")
df_ht = read_csv_with_fallback(DATA_DIR / "Herb_target.csv")
df_hh = read_csv_with_fallback(DATA_DIR / "herbherb.csv")
df_hs = read_csv_with_fallback(DATA_DIR / "herb-symptom.csv")
df_he = read_csv_with_fallback(DATA_DIR / "herb_efficiacy.csv")

print(f"草药-成分关系数: {len(df_hc)}")
print(f"草药-靶点关系数: {len(df_ht)}")
print(f"草药-草药关系数: {len(df_hh)}")
print(f"草药-症状关系数: {len(df_hs)}")
print(f"草药-功效关系数: {len(df_he)}")

# ==================== 2. 列名映射 ====================
hc_herb_col = 'Herb ID'
hc_compound_col = 'Pref Name'
if hc_compound_col not in df_hc.columns:
    hc_compound_col = 'Compound Id'

ht_herb_col = 'Herb ID'
ht_target_col = 'Gene Symbol'

# 检查必需列
if hc_herb_col not in df_hc.columns:
    raise ValueError(f"herb_compound.csv 缺少必需列: {hc_herb_col}")
if hc_compound_col not in df_hc.columns:
    raise ValueError(f"herb_compound.csv 缺少必需列: {hc_compound_col}")
if ht_herb_col not in df_ht.columns:
    raise ValueError(f"Herb_target.csv 缺少必需列: {ht_herb_col}")
if ht_target_col not in df_ht.columns:
    raise ValueError(f"Herb_target.csv 缺少必需列: {ht_target_col}")

# ==================== 3. 构建草药拉丁名映射（仅保留非空） ====================
herb_name_map = {}
for _, row in df_ht.iterrows():
    herb_id = str(row['Herb ID'])
    latin_name = row['Latin_name']
    if pd.notna(latin_name) and str(latin_name).strip():
        herb_name_map[herb_id] = str(latin_name)

# 所有草药ID（出现在成分或靶点关系中的）
all_herb_ids = set(df_hc[hc_herb_col]).union(set(df_ht[ht_herb_col]))

# ==================== 4. 提取节点 ====================
nodes = []

# 4.1 草药节点（仅添加有拉丁名的）
for hid in all_herb_ids:
    latin = herb_name_map.get(str(hid))
    if latin:
        nodes.append({'id': str(hid), 'type': 'Herb', 'name': latin})

# 4.2 成分节点
compounds = set(df_hc[hc_compound_col])
for c in compounds:
    nodes.append({'id': str(c), 'type': 'Ingredient', 'name': str(c)})

# 4.3 靶点节点
targets = set(df_ht[ht_target_col])
for t in targets:
    nodes.append({'id': str(t), 'type': 'Target', 'name': str(t)})

# 4.4 症状节点（从 herb-symptom.csv 中提取，去除前后空格）
symptoms = set()
for _, row in df_hs.iterrows():
    sym = row['symptom']   # 现在列名已 clean
    if pd.notna(sym):
        symptoms.add(str(sym).strip())
for sym in symptoms:
    nodes.append({'id': sym, 'type': 'Symptom', 'name': sym})

# 4.5 功效节点
efficacies = set()
for _, row in df_he.iterrows():
    eff = row['efficacy']   # 列名已 clean
    if pd.notna(eff):
        efficacies.add(str(eff).strip())
for eff in efficacies:
    nodes.append({'id': eff, 'type': 'Efficacy', 'name': eff})

# ==================== 5. 提取关系 ====================
relations = []

# 5.1 Herb -> Ingredient
for _, row in df_hc.iterrows():
    source = str(row[hc_herb_col])
    if source in herb_name_map:
        relations.append({
            'source': source,
            'source_type': 'Herb',
            'target': str(row[hc_compound_col]),
            'target_type': 'Ingredient',
            'relation': 'CONTAINS_INGREDIENT'
        })

# 5.2 Herb -> Target
for _, row in df_ht.iterrows():
    source = str(row[ht_herb_col])
    if source in herb_name_map:
        relations.append({
            'source': source,
            'source_type': 'Herb',
            'target': str(row[ht_target_col]),
            'target_type': 'Target',
            'relation': 'TARGETS'
        })

# 5.3 Herb -> Symptom (RELIEVES)
for _, row in df_hs.iterrows():
    herb_id = str(row['Herb_id']).strip() if pd.notna(row['Herb_id']) else None
    symptom = str(row['symptom']).strip() if pd.notna(row['symptom']) else None
    if herb_id and symptom and herb_id in herb_name_map:
        relations.append({
            'source': herb_id,
            'source_type': 'Herb',
            'target': symptom,
            'target_type': 'Symptom',
            'relation': 'RELIEVES'
        })

# 5.4 Herb -> Efficacy (HAS_EFFICACY)
for _, row in df_he.iterrows():
    herb_id = str(row['herb']).strip() if pd.notna(row['herb']) else None
    efficacy = str(row['efficacy']).strip() if pd.notna(row['efficacy']) else None
    if herb_id and efficacy and herb_id in herb_name_map:
        relations.append({
            'source': herb_id,
            'source_type': 'Herb',
            'target': efficacy,
            'target_type': 'Efficacy',
            'relation': 'HAS_EFFICACY'
        })

# 5.5 Herb <-> Herb (PAIRS_WITH)
for _, row in df_hh.iterrows():
    h1 = str(row['herb1']).strip() if pd.notna(row['herb1']) else None
    h2 = str(row['herb2']).strip() if pd.notna(row['herb2']) else None
    if h1 and h2 and h1 in herb_name_map and h2 in herb_name_map:
        relations.append({
            'source': h1,
            'source_type': 'Herb',
            'target': h2,
            'target_type': 'Herb',
            'relation': 'PAIRS_WITH'
        })
        relations.append({
            'source': h2,
            'source_type': 'Herb',
            'target': h1,
            'target_type': 'Herb',
            'relation': 'PAIRS_WITH'
        })

# ==================== 6. 去重并保存 ====================
nodes_df = pd.DataFrame(nodes).drop_duplicates(subset=['id'])
rels_df = pd.DataFrame(relations).drop_duplicates()

nodes_df.to_csv(PROCESSED_DIR / "tcmsp_nodes.csv", index=False, encoding='utf-8-sig')
rels_df.to_csv(PROCESSED_DIR / "tcmsp_rels.csv", index=False, encoding='utf-8-sig')

print(f"节点总数: {len(nodes_df)}")
print(f"关系总数: {len(rels_df)}")
print("节点类型分布:")
print(nodes_df['type'].value_counts())