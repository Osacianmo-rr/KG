#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据质量分析脚本
用途：统计 PubMed 文献集的各项分布指标，为数据清洗和实体抽取提供依据。
输入：data/raw/pubmed_tcm_depression_v2.csv
输出：data/processed/dataset_report.xlsx (多 sheet Excel)
      data/processed/dataset_statistics.csv (总体统计)
"""

import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import numpy as np

# 配置路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = RAW_DATA_DIR / "pubmed_tcm_depression_v2.csv"
OUTPUT_EXCEL = PROCESSED_DIR / "dataset_report.xlsx"
OUTPUT_CSV_STATS = PROCESSED_DIR / "dataset_statistics.csv"


def load_data() -> pd.DataFrame:
    """加载 CSV 数据，处理缺失值和基本类型"""
    if not INPUT_CSV.exists():
        print(f"错误：找不到输入文件 {INPUT_CSV}")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    print(f"成功加载 {len(df)} 条文献记录")
    return df


def analyze_years(df: pd.DataFrame) -> pd.DataFrame:
    """年份分布统计"""
    # 处理 Year 列，将缺失值标记为 'Unknown'
    years = df["Year"].fillna("Unknown").astype(str)
    # 过滤掉非数字的年份（例如空字符串或 'Unknown'）
    valid_years = years[years.str.match(r"^\d{4}$")]

    year_counts = valid_years.value_counts().sort_index().reset_index()
    year_counts.columns = ["Year", "Count"]
    total_with_year = valid_years.count()
    total_missing = len(df) - total_with_year

    # 附加说明行
    note_df = pd.DataFrame([
        ["Total papers", len(df)],
        ["Papers with valid year", total_with_year],
        ["Papers missing year", total_missing]
    ], columns=["Metric", "Value"])

    return year_counts, note_df


def analyze_journals(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """期刊分布统计，返回前 top_n 个期刊及其占比"""
    journal_counts = df["Journal"].value_counts().reset_index()
    journal_counts.columns = ["Journal", "Count"]
    journal_counts["Percentage"] = (journal_counts["Count"] / len(df) * 100).round(2)
    # 可选：只保留前 top_n 条（全部也可以，但 Excel 可能太大）
    return journal_counts.head(top_n)


def analyze_source_queries(df: pd.DataFrame) -> pd.DataFrame:
    """
    检索式分布统计：将 SourceQueries 列按分号拆分，统计每个检索式标签出现的文献数。
    （一篇文献可能属于多个检索式，每个标签独立计数）
    """
    # 处理缺失值
    source_series = df["SourceQueries"].fillna("")
    label_counter = Counter()

    for source_str in source_series:
        if not source_str.strip():
            continue
        # 按分号拆分并去除首尾空格
        labels = [lab.strip() for lab in source_str.split(";") if lab.strip()]
        label_counter.update(labels)

    # 转为 DataFrame
    label_df = pd.DataFrame(label_counter.most_common(), columns=["QueryLabel", "Count"])
    label_df["Percentage"] = (label_df["Count"] / len(df) * 100).round(2)
    return label_df


def analyze_abstract_length(df: pd.DataFrame) -> pd.DataFrame:
    """摘要长度统计（字符数）"""
    # 将 Abstract 填充为空字符串
    abstracts = df["Abstract"].fillna("").astype(str)
    lengths = abstracts.str.len()

    stats = {
        "Num of papers": len(df),
        "Papers with abstract": (lengths > 0).sum(),
        "Papers without abstract": (lengths == 0).sum(),
        "Min length (characters)": lengths.min(),
        "Max length": lengths.max(),
        "Mean length": lengths.mean(),
        "Median length": lengths.median(),
        "Std length": lengths.std(),
    }
    stats_df = pd.DataFrame([stats]).T.reset_index()
    stats_df.columns = ["Metric", "Value"]
    return stats_df


def analyze_publication_types(df: pd.DataFrame) -> pd.DataFrame:
    """文献类型分布（PublicationTypes 列，按分号拆分统计）"""
    pub_series = df["PublicationTypes"].fillna("")
    type_counter = Counter()

    for pub_str in pub_series:
        if not pub_str.strip():
            continue
        types = [t.strip() for t in pub_str.split(";") if t.strip()]
        type_counter.update(types)

    type_df = pd.DataFrame(type_counter.most_common(), columns=["PublicationType", "Count"])
    type_df["Percentage"] = (type_df["Count"] / len(df) * 100).round(2)
    return type_df


def overall_summary(df: pd.DataFrame) -> pd.DataFrame:
    """总体统计摘要（作为 CSV 或第一个 sheet）"""
    # 计算作者数量分布（可选）
    authors_series = df["Authors"].fillna("")
    num_authors = authors_series.str.split(";").apply(len)
    num_authors = num_authors[num_authors > 0]  # 排除空作者

    summary = {
        "Total papers": len(df),
        "Papers with DOI": df["DOI"].notna().sum(),
        "Papers with abstract": df["Abstract"].notna().sum(),
        "Papers with journal": df["Journal"].notna().sum(),
        "Papers with year": df["Year"].notna().sum(),
        "Distinct journals": df["Journal"].nunique(),
        "Distinct years": df["Year"].nunique(),
        "Min authors per paper": num_authors.min(),
        "Max authors per paper": num_authors.max(),
        "Mean authors per paper": round(num_authors.mean(), 2),
        "Median authors per paper": num_authors.median(),
    }
    return pd.DataFrame([summary]).T.reset_index().rename(columns={0: "Value", "index": "Metric"})


def main():
    print("=" * 60)
    print("数据质量分析工具")
    print("=" * 60)

    # 1. 加载数据
    df = load_data()

    # 2. 进行各项分析
    print("正在分析年份分布...")
    year_dist, year_note = analyze_years(df)

    print("正在分析期刊分布（前20）...")
    journal_dist = analyze_journals(df, top_n=20)

    print("正在分析检索式分布...")
    query_dist = analyze_source_queries(df)

    print("正在分析摘要长度...")
    abstract_stats = analyze_abstract_length(df)

    print("正在分析文献类型分布...")
    pubtype_dist = analyze_publication_types(df)

    print("正在生成总体摘要...")
    overall = overall_summary(df)

    # 3. 保存到 Excel（多个 sheet）
    print(f"\n保存报告至 {OUTPUT_EXCEL}")
    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        overall.to_excel(writer, sheet_name="Overall Summary", index=False)
        year_dist.to_excel(writer, sheet_name="Year Distribution", index=False)
        year_note.to_excel(writer, sheet_name="Year Missing Info", index=False)
        journal_dist.to_excel(writer, sheet_name="Journal Distribution (Top20)", index=False)
        query_dist.to_excel(writer, sheet_name="Query Label Distribution", index=False)
        abstract_stats.to_excel(writer, sheet_name="Abstract Length Stats", index=False)
        pubtype_dist.to_excel(writer, sheet_name="Publication Types", index=False)

    # 4. 同时保存总体统计为 CSV（便于后续读取）
    overall.to_csv(OUTPUT_CSV_STATS, index=False, encoding="utf-8-sig")
    print(f"总体统计 CSV 保存至 {OUTPUT_CSV_STATS}")

    # 5. 打印简表到控制台
    print("\n===== 总体摘要 =====")
    for _, row in overall.iterrows():
        print(f"{row['Metric']}: {row['Value']}")

    print("\n===== 检索式分布（前5） =====")
    print(query_dist.head(5).to_string(index=False))

    print("\n===== 文献类型分布（前5） =====")
    print(pubtype_dist.head(5).to_string(index=False))

    print("\n✅ 分析完成！")


if __name__ == "__main__":
    main()