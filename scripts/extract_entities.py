#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阶段8：基于词典的实体抽取（自动扫描 dictionaries 目录）
输入：data/processed/high_quality_corpus.csv
输出：data/processed/entities.csv
"""

import re
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DICT_DIR = PROJECT_ROOT / "data" / "dictionaries"
INPUT_CSV = DATA_PROCESSED / "high_quality_corpus.csv"
OUTPUT_CSV = DATA_PROCESSED / "entities.csv"


# ---------- 加载 herb（含别名映射）----------
def load_herb_mapping():
    """
    加载 herb 标准名和别名映射
    返回: alias_map (dict, alias_lower -> standard_name)
    """
    # 加载标准名（herb.txt）
    herb_standard = set()
    herb_path = DICT_DIR / "herb.txt"
    if herb_path.exists():
        with open(herb_path, 'r', encoding='utf-8') as f:
            herb_standard = {line.strip().lower() for line in f if line.strip()}

    # 加载别名映射（herb_alias.csv）
    alias_map = {}
    alias_path = DICT_DIR / "herb_alias.csv"
    if alias_path.exists():
        df = pd.read_csv(alias_path, encoding='utf-8-sig')
        for _, row in df.iterrows():
            alias = str(row['alias']).strip().lower()
            std = str(row['standard_name']).strip()
            if alias and std:
                alias_map[alias] = std

    # 将标准名自身也加入映射（以便直接匹配标准名）
    for std in herb_standard:
        alias_map[std.lower()] = std

    return alias_map


# ---------- 加载其他词典（自动扫描 .txt 文件）----------
def load_other_dictionaries():
    """
    扫描 dictionaries 目录下所有 .txt 文件（排除 herb.txt 和 herb_alias.csv）
    返回: dict {entity_type: set_of_terms_lowercase}
    """
    other_dicts = {}
    for txt_file in DICT_DIR.glob("*.txt"):
        if txt_file.name == "herb.txt":
            continue  # herb 单独处理
        entity_type = txt_file.stem  # 文件名（不含扩展名）作为类型，例如 disease, formula
        with open(txt_file, 'r', encoding='utf-8') as f:
            terms = {line.strip().lower() for line in f if line.strip()}
        if terms:
            other_dicts[entity_type] = terms
        else:
            print(f"警告：词典 {txt_file.name} 为空，跳过")
    return other_dicts


# ---------- 编译正则（长词优先）----------
def build_regex_patterns(terms_dict):
    """
    输入: {entity_type: set_of_terms}
    输出: list of (entity_type, compiled_pattern)
    """
    patterns = []
    for etype, terms in terms_dict.items():
        if not terms:
            continue
        # 按长度降序排序
        sorted_terms = sorted(terms, key=len, reverse=True)
        escaped = [re.escape(term) for term in sorted_terms]
        pattern = re.compile(r'\b(' + '|'.join(escaped) + r')\b', re.IGNORECASE)
        patterns.append((etype, pattern))
    return patterns


# ---------- 实体抽取 ----------
def extract_entities_from_text(text, herb_alias_map, other_patterns):
    """
    从文本中抽取实体
    返回: list of (entity_text, entity_type, standard_form)
    """
    if not isinstance(text, str):
        return []
    text_lower = text.lower()
    entities = []
    used_spans = []  # 避免同一位置多次匹配（仅用于 herb 自身去重）

    # 1. 抽取 herb（使用别名映射）
    herb_keys = sorted(herb_alias_map.keys(), key=len, reverse=True)
    if herb_keys:
        herb_pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in herb_keys) + r')\b', re.IGNORECASE)
        for match in herb_pattern.finditer(text_lower):
            matched = match.group(0)
            start, end = match.span()
            # 去重：避免同一位置重复匹配（如别名和标准名相同）
            overlap = False
            for s, e, _, _ in used_spans:
                if not (end <= s or start >= e):
                    overlap = True
                    break
            if not overlap:
                standard = herb_alias_map[matched]
                entities.append((matched, "Herb", standard))
                used_spans.append((start, end, standard, "Herb"))

    # 2. 抽取其他实体类型
    for etype, pattern in other_patterns:
        for match in pattern.finditer(text_lower):
            matched = match.group(0)
            # 对于非 herb 实体，standard_form 直接使用匹配到的原始词（小写）
            entities.append((matched, etype.capitalize(), matched))

    # 去重：基于 (standard_form, entity_type)
    seen = set()
    unique = []
    for ent in entities:
        key = (ent[2].lower(), ent[1])
        if key not in seen:
            seen.add(key)
            unique.append(ent)
    return unique


# ---------- 主函数 ----------
def main():
    print("加载词典...")
    herb_alias_map = load_herb_mapping()
    print(f"  Herb 别名+标准名总数: {len(herb_alias_map)}")

    other_dicts = load_other_dictionaries()
    print("  其他词典:", list(other_dicts.keys()))

    other_patterns = build_regex_patterns(other_dicts)

    print("加载文献数据...")
    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    print(f"共 {len(df)} 篇文献")

    all_entities = []
    for idx, row in df.iterrows():
        pmid = row['PMID']
        title = str(row.get('Title', ''))
        abstract = str(row.get('Abstract', ''))
        full_text = title + " " + abstract
        if not full_text.strip():
            continue
        entities = extract_entities_from_text(full_text, herb_alias_map, other_patterns)
        for ent_text, ent_type, standard_form in entities:
            all_entities.append({
                'PMID': pmid,
                'Entity': standard_form,
                'Type': ent_type
            })

    out_df = pd.DataFrame(all_entities)
    out_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"实体抽取完成，共提取 {len(out_df)} 条实体记录，保存至 {OUTPUT_CSV}")

    if not out_df.empty:
        print("\n实体类型分布：")
        print(out_df['Type'].value_counts())
    else:
        print("警告：未提取到任何实体，请检查词典内容是否匹配文本。")


if __name__ == "__main__":
    main()