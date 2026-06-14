#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阶段6：构建高质量语料库
- 统计标注结果（相关/不相关数量）
- 生成只包含相关文献的高质量语料库
"""

import pandas as pd
from pathlib import Path

# 配置路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "to_label.csv"  # 修改为你的标注文件路径
OUTPUT_STATS = PROJECT_ROOT / "data" / "processed" / "label_stats.txt"
OUTPUT_CORPUS = PROJECT_ROOT / "data" / "processed" / "high_quality_corpus.csv"


def main():
    # 1. 读取标注结果
    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    print(f"总文献数：{len(df)}")

    # 2. 检查 Label 列是否存在且无空值
    if "Label" not in df.columns:
        raise ValueError("CSV 中缺少 'Label' 列，请检查文件格式。")
    if df["Label"].isnull().any():
        print("警告：Label 列存在空值，将自动填充为 0（不相关）")
        df["Label"] = df["Label"].fillna(0).astype(int)

    # 3. 统计
    label_counts = df["Label"].value_counts().to_dict()
    relevant = label_counts.get(1, 0)
    irrelevant = label_counts.get(0, 0)
    print(f"Label=1 (相关): {relevant} 篇")
    print(f"Label=0 (不相关): {irrelevant} 篇")

    # 4. 保存统计结果
    with open(OUTPUT_STATS, "w", encoding="utf-8") as f:
        f.write(f"总文献数：{len(df)}\n")
        f.write(f"相关文献数 (Label=1)：{relevant}\n")
        f.write(f"不相关文献数 (Label=0)：{irrelevant}\n")
        f.write(f"相关率：{relevant / len(df) * 100:.1f}%\n")
    print(f"统计结果已保存到：{OUTPUT_STATS}")

    # 5. 生成高质量语料库（只保留 Label=1 的文献）
    corpus_df = df[df["Label"] == 1].copy()
    # 可选：删除 Label 列（因为后续不再需要）
    # corpus_df = corpus_df.drop(columns=["Label"])
    corpus_df.to_csv(OUTPUT_CORPUS, index=False, encoding="utf-8-sig")
    print(f"高质量语料库已保存到：{OUTPUT_CORPUS} (共 {len(corpus_df)} 篇)")


if __name__ == "__main__":
    main()