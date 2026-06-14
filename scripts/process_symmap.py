#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
处理 SymMap v2.0 数据，生成 nodes.csv 和 relations.csv
自动适应常见列名，修复路径和 concat 错误
"""

import pandas as pd
from pathlib import Path

# 获取项目根目录（scripts 的父目录）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYMMAP_DIR = PROJECT_ROOT / "data" / "symmap"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# 文件路径（使用绝对路径）
SMHB_FILE = SYMMAP_DIR / "SymMap v2.0, SMHB file.xlsx"
SMIT_FILE = SYMMAP_DIR / "SymMap v2.0, SMIT file.xlsx"
SMTT_FILE = SYMMAP_DIR / "SymMap v2.0, SMTT file.xlsx"

OUTPUT_NODES = PROCESSED_DIR / "final_nodes.csv"
OUTPUT_RELATIONS = PROCESSED_DIR / "final_relations.csv"


def main():
    print("正在加载 SymMap 文件...")

    # 读取文件
    df_smhb = pd.read_excel(SMHB_FILE, engine='openpyxl')
    df_smit = pd.read_excel(SMIT_FILE, engine='openpyxl')
    df_smtt = pd.read_excel(SMTT_FILE, engine='openpyxl')

    print(f"SMHB 形状: {df_smhb.shape}")
    print(f"SMIT 形状: {df_smit.shape}")
    print(f"SMTT 形状: {df_smtt.shape}")

    # 打印列名供调试
    print("\nSMHB 列名:", list(df_smhb.columns))
    print("SMIT 列名:", list(df_smit.columns))
    print("SMTT 列名:", list(df_smtt.columns))

    # 打印前两行数据（可选）
    # print("\nSMHB 前2行:\n", df_smhb.head(2))
    # print("SMIT 前2行:\n", df_smit.head(2))
    # print("SMTT 前2行:\n", df_smtt.head(2))

    # ================= 提取节点 =================

    # ---- 草药节点 ----
    # 通常 SMHB 的第一列是草药 ID 或名称，假设列名包含 'Herb' 或第一列
    herb_col = None
    for col in df_smhb.columns:
        if 'herb' in col.lower():
            herb_col = col
            break
    if herb_col is None:
        herb_col = df_smhb.columns[0]  # 取第一列

    herbs = df_smhb[[herb_col]].drop_duplicates().copy()
    herbs.columns = ['name']  # 统一列名
    herbs['type'] = 'Herb'
    herbs['id'] = herbs['name'].astype(str)
    print(f"草药节点数: {len(herbs)}")

    # ---- 成分节点 ----
    # SMIT 通常有 Ingredient_ID 和 Ingredient_Name 两列
    ing_id_col = None
    ing_name_col = None
    for col in df_smit.columns:
        if 'id' in col.lower() and ('ingredient' in col.lower() or 'compound' in col.lower()):
            ing_id_col = col
        if 'name' in col.lower() and ('ingredient' in col.lower() or 'compound' in col.lower()):
            ing_name_col = col
    if ing_id_col is None:
        # 尝试找包含 'ID' 的列
        for col in df_smit.columns:
            if 'id' in col.lower():
                ing_id_col = col
                break
    if ing_name_col is None:
        # 尝试找包含 'Name' 的列
        for col in df_smit.columns:
            if 'name' in col.lower():
                ing_name_col = col
                break
    if ing_id_col is None:
        ing_id_col = df_smit.columns[0]
    if ing_name_col is None:
        ing_name_col = df_smit.columns[1] if len(df_smit.columns) > 1 else ing_id_col

    ingredients = df_smit[[ing_id_col, ing_name_col]].drop_duplicates(subset=[ing_id_col]).copy()
    ingredients = ingredients.rename(columns={ing_id_col: 'id', ing_name_col: 'name'})
    ingredients['type'] = 'Ingredient'
    # 确保 id 是字符串
    ingredients['id'] = ingredients['id'].astype(str)
    print(f"成分节点数: {len(ingredients)}")

    # ---- 靶点节点 ----
    # SMTT 通常有 Target_ID 和 Target_Name/Gene_Name
    tar_id_col = None
    tar_name_col = None
    for col in df_smtt.columns:
        if 'id' in col.lower() and ('target' in col.lower() or 'uniprot' in col.lower()):
            tar_id_col = col
        if 'name' in col.lower() or 'gene' in col.lower():
            tar_name_col = col
    if tar_id_col is None:
        for col in df_smtt.columns:
            if 'id' in col.lower():
                tar_id_col = col
                break
    if tar_name_col is None:
        for col in df_smtt.columns:
            if 'name' in col.lower() or 'gene' in col.lower():
                tar_name_col = col
                break
    if tar_id_col is None:
        tar_id_col = df_smtt.columns[0]
    if tar_name_col is None:
        tar_name_col = df_smtt.columns[1] if len(df_smtt.columns) > 1 else tar_id_col

    targets = df_smtt[[tar_id_col, tar_name_col]].drop_duplicates(subset=[tar_id_col]).copy()
    targets = targets.rename(columns={tar_id_col: 'id', tar_name_col: 'name'})
    targets['type'] = 'Target'
    targets['id'] = targets['id'].astype(str)
    print(f"靶点节点数: {len(targets)}")

    # 合并节点：确保列一致
    herbs = herbs[['id', 'name', 'type']]
    ingredients = ingredients[['id', 'name', 'type']]
    targets = targets[['id', 'name', 'type']]

    # 使用 pd.concat 并重置索引，忽略重复索引问题
    all_nodes = pd.concat([herbs, ingredients, targets], ignore_index=True)
    all_nodes = all_nodes.drop_duplicates(subset=['id'])
    print(f"总节点数: {len(all_nodes)}")

    # ================= 生成关系 =================
    relations = []

    # ---- 草药 -> 成分 ----
    # 寻找 SMHB 中关联成分的列
    ing_col_in_smhb = None
    for col in df_smhb.columns:
        if 'ingredient' in col.lower() or 'compound' in col.lower() or 'molecule' in col.lower():
            ing_col_in_smhb = col
            break
    if ing_col_in_smhb is None:
        # 尝试第二列（通常第一列是草药，第二列是成分）
        if len(df_smhb.columns) >= 2:
            ing_col_in_smhb = df_smhb.columns[1]

    if ing_col_in_smhb is not None:
        # 获取草药列和成分列
        herb_col_in_smhb = herb_col
        temp = df_smhb[[herb_col_in_smhb, ing_col_in_smhb]].drop_duplicates().dropna()
        for _, row in temp.iterrows():
            herb_name = str(row[herb_col_in_smhb])
            ing_value = str(row[ing_col_in_smhb])
            # 尝试匹配成分 ID 或名称
            # 首先尝试直接匹配 ingredients 中的 id
            if ing_value in ingredients['id'].values:
                ing_id = ing_value
            else:
                # 尝试匹配名称
                match = ingredients[ingredients['name'] == ing_value]
                if not match.empty:
                    ing_id = match.iloc[0]['id']
                else:
                    # 如果都匹配不上，跳过（或者保留原值，但可能导致孤立节点）
                    continue
            relations.append({
                'source': herb_name,
                'source_type': 'Herb',
                'target': ing_id,
                'target_type': 'Ingredient',
                'relation': 'CONTAINS_INGREDIENT'
            })
    else:
        print("警告: SMHB 中未找到成分列，跳过草药-成分关系")

    print(f"草药-成分关系数: {len(relations)}")

    # ---- 成分 -> 靶点 ----
    # 寻找 SMHB 中关联靶点的列（或者从 SMIT 中关联靶点）
    target_col_in_smhb = None
    for col in df_smhb.columns:
        if 'target' in col.lower():
            target_col_in_smhb = col
            break
    if target_col_in_smhb is not None:
        # 使用 SMHB 中的成分-靶点映射
        temp = df_smhb[[ing_col_in_smhb, target_col_in_smhb]].drop_duplicates().dropna()
        for _, row in temp.iterrows():
            ing_value = str(row[ing_col_in_smhb])
            tar_value = str(row[target_col_in_smhb])
            # 匹配成分 ID
            if ing_value in ingredients['id'].values:
                ing_id = ing_value
            else:
                match = ingredients[ingredients['name'] == ing_value]
                if not match.empty:
                    ing_id = match.iloc[0]['id']
                else:
                    continue
            # 匹配靶点 ID
            if tar_value in targets['id'].values:
                tar_id = tar_value
            else:
                match = targets[targets['name'] == tar_value]
                if not match.empty:
                    tar_id = match.iloc[0]['id']
                else:
                    continue
            relations.append({
                'source': ing_id,
                'source_type': 'Ingredient',
                'target': tar_id,
                'target_type': 'Target',
                'relation': 'ACTS_ON'
            })
    else:
        # 备选：如果 SMHB 没有靶点列，尝试从 SMIT 中提取（但 SMIT 通常没有靶点列）
        print("警告: SMHB 中未找到靶点列，成分-靶点关系将为空")

    print(f"成分-靶点关系数: {len(relations) - (草药 - 成分关系数)}")

    # 保存结果
    all_nodes.to_csv(OUTPUT_NODES, index=False, encoding='utf-8-sig')
    pd.DataFrame(relations).to_csv(OUTPUT_RELATIONS, index=False, encoding='utf-8-sig')

    print(f"\n节点文件: {OUTPUT_NODES}")
    print(f"关系文件: {OUTPUT_RELATIONS}")
    print("\n节点类型分布:")
    print(all_nodes['type'].value_counts())
    print(f"\n总关系数: {len(relations)}")


if __name__ == "__main__":
    main()