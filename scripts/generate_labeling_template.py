#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从完整数据集中随机抽取50篇文献，生成标注模板（Excel文件）。
每一行包含 PMID、Title 和一个空的 Relevant 列（后续人工填写 1 或 0）。
"""

import random
from pathlib import Path

import pandas as pd

# 配置路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
INPUT_CSV = RAW_DATA_DIR / "pubmed_tcm_depression_v2.csv"
OUTPUT_TEMPLATE = PROJECT_ROOT / "data" / "processed" / "labeling_sample_50.xlsx"

# 设置随机种子，保证每次运行抽取结果可复现（可选）
random.seed(42)

def main():
    # 1. 读取完整数据
    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    print(f"总文献数：{len(df)}")

    # 2. 随机抽取 50 篇（如果总数不足50，则抽取全部，但这里733>50）
    if len(df) < 50:
        sample_df = df
    else:
        sample_df = df.sample(n=50, random_state=42)  # random_state 保证每次抽的一样

    # 3. 只保留需要的列：PMID, Title，并添加空的 Relevant 列
    sample_df = sample_df[["PMID", "Title"]].copy()
    sample_df["Relevant"] = ""   # 留空，人工填写 1 或 0

    # 4. 保存为 Excel，方便人工标注
    # 为了更友好，可以设置数据验证（下拉选项），但非必须；这里直接保存
    sample_df.to_excel(OUTPUT_TEMPLATE, index=False, sheet_name="Sample")
    print(f"已生成标注模板：{OUTPUT_TEMPLATE}")
    print(f"共 {len(sample_df)} 篇文献，请打开文件，在 Relevant 列标注：1=相关，0=不相关")

if __name__ == "__main__":
    main()