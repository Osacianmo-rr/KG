#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据清洗脚本：
1. 自动删除空标题、空摘要、摘要过短（<100字符）、重复PMID
2. 生成带 Label 列的 CSV 供人工标记“是否与中医药抑郁症相关”
3. 应用人工标记结果，输出最终干净数据集
"""

import argparse
from pathlib import Path

import pandas as pd

# 路径配置
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = RAW_DATA_DIR / "pubmed_tcm_depression_v2.csv"
AUTO_CLEANED_CSV = PROCESSED_DIR / "auto_cleaned.csv"
TO_LABEL_CSV = PROCESSED_DIR / "to_label.csv"
FINAL_CLEAN_CSV = PROCESSED_DIR / "clean_pubmed.csv"


def auto_clean():
    """执行自动清洗：删除空标题、空摘要、短摘要、重复PMID"""
    print("=" * 60)
    print("步骤1：自动清洗")
    print("=" * 60)

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    original_count = len(df)
    print(f"原始文献数：{original_count}")

    # 删除 Title 为空
    before = len(df)
    df = df[df["Title"].notna() & (df["Title"].str.strip() != "")]
    print(f"删除空标题后：{len(df)} (删除 {before - len(df)} 条)")

    # 删除 Abstract 为空
    before = len(df)
    df = df[df["Abstract"].notna() & (df["Abstract"].str.strip() != "")]
    print(f"删除空摘要后：{len(df)} (删除 {before - len(df)} 条)")

    # 删除 Abstract 长度 < 100 字符
    before = len(df)
    df["Abstract_len"] = df["Abstract"].astype(str).str.len()
    df = df[df["Abstract_len"] >= 100]
    print(f"删除短摘要（<100字符）后：{len(df)} (删除 {before - len(df)} 条)")
    df = df.drop(columns=["Abstract_len"])

    # 删除重复 PMID（保留第一次出现）
    before = len(df)
    df = df.drop_duplicates(subset=["PMID"], keep="first")
    print(f"删除重复PMID后：{len(df)} (删除 {before - len(df)} 条)")

    # 保存自动清洗后的文件（备用）
    df.to_csv(AUTO_CLEANED_CSV, index=False, encoding="utf-8-sig")
    print(f"自动清洗后数据已保存至：{AUTO_CLEANED_CSV}")

    # 生成待人工标记的文件（只保留关键字段，添加空的 Label 列）
    to_label = df[["PMID", "Title", "Abstract"]].copy()
    to_label["Label"] = ""  # 人工填写 1=保留，0=删除
    to_label.to_csv(TO_LABEL_CSV, index=False, encoding="utf-8-sig")
    print(f"待标记文件已生成：{TO_LABEL_CSV}")
    print("\n请用 Excel 打开该文件，在 Label 列填写 1（保留）或 0（删除），保存后重新运行脚本并加上 --apply-labels 参数。")
    print("例如：python scripts/clean_pubmed.py --apply-labels\n")


def apply_labels():
    """读取人工标记后的文件，生成最终干净数据集"""
    print("=" * 60)
    print("步骤2：应用人工标记")
    print("=" * 60)

    if not TO_LABEL_CSV.exists():
        print(f"错误：找不到 {TO_LABEL_CSV}，请先运行自动清洗生成标记文件。")
        return

    df_label = pd.read_csv(TO_LABEL_CSV, encoding="utf-8-sig")
    # 检查 Label 列是否有未填写的
    missing = df_label["Label"].isna() | (df_label["Label"].astype(str).str.strip() == "")
    if missing.any():
        print(f"警告：Label 列存在 {missing.sum()} 个空值，请填写完整后再运行。")
        return

    # 转换为整数
    df_label["Label"] = df_label["Label"].astype(int)
    kept = df_label[df_label["Label"] == 1]
    print(f"人工标记结果：总 {len(df_label)} 篇，保留 {len(kept)} 篇，删除 {len(df_label) - len(kept)} 篇")

    # 获取自动清洗后的完整数据（包含所有字段）
    if not AUTO_CLEANED_CSV.exists():
        print(f"错误：找不到 {AUTO_CLEANED_CSV}，请先运行自动清洗。")
        return

    df_full = pd.read_csv(AUTO_CLEANED_CSV, encoding="utf-8-sig")
    # 只保留标记为 1 的 PMID
    final_df = df_full[df_full["PMID"].isin(kept["PMID"])]
    print(f"最终干净数据集：{len(final_df)} 篇")

    final_df.to_csv(FINAL_CLEAN_CSV, index=False, encoding="utf-8-sig")
    print(f"已保存至：{FINAL_CLEAN_CSV}")


def main():
    parser = argparse.ArgumentParser(description="PubMed 数据清洗工具")
    parser.add_argument("--apply-labels", action="store_true", help="应用人工标记结果生成最终干净数据集")
    args = parser.parse_args()

    if args.apply_labels:
        apply_labels()
    else:
        auto_clean()


if __name__ == "__main__":
    main()