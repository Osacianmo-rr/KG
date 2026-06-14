#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动修复 final_nodes.csv 中的脏数据行和重复节点
"""

import pandas as pd
from pathlib import Path


def repair_final_nodes(input_path, output_path=None):
    """
    读取 final_nodes.csv，删除脏数据行（如 "Herb ID,Herb,Latin_name"），
    并按 id 去重，保留第一次出现的节点。
    """
    if output_path is None:
        output_path = input_path.parent / "final_nodes_fixed.csv"

    # 读取文件（第一行应为 id,type,name）
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    print(f"原始节点数: {len(df)}")

    # 1. 删除脏数据行：id 列中包含 "Herb ID" 或 "Latin_name" 的行
    #    （这些行的 id 通常是字符串 "Herb ID" 或其他列名字符串）
    mask = ~df['id'].astype(str).str.contains('Herb ID|Latin_name', case=False, na=False)
    df_clean = df[mask]
    print(f"删除脏数据行后节点数: {len(df_clean)}")

    # 2. 按 id 去重，保留第一次出现的记录
    df_clean = df_clean.drop_duplicates(subset=['id'], keep='first')
    print(f"去重后节点数: {len(df_clean)}")

    # 3. 保存修复后的文件
    df_clean.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"修复后的文件已保存至: {output_path}")

    return df_clean


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[1]  # 假设脚本放在 scripts/ 下
    INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "final_nodes.csv"
    OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "final_nodes_fixed.csv"

    repair_final_nodes(INPUT_FILE, OUTPUT_FILE)