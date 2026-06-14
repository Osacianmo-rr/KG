#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
合并所有来源：文献实体 + 论文节点 + 模拟网络（herb->ingredient->target）
输出 final_nodes.csv 和 final_relations.csv
"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"

# 输入文件
ENTITIES_CSV = PROCESSED_DIR / "entities.csv"
PAPERS_CSV = PROCESSED_DIR / "high_quality_corpus.csv"
MOCK_HI_CSV = EXTERNAL_DIR / "mock_herb_ingredient.csv"
MOCK_IT_CSV = EXTERNAL_DIR / "mock_ingredient_target.csv"

# 输出文件
OUTPUT_NODES = PROCESSED_DIR / "final_nodes.csv"
OUTPUT_RELATIONS = PROCESSED_DIR / "final_relations.csv"

def main():
    print("1. 加载文献实体...")
    df_entities = pd.read_csv(ENTITIES_CSV, encoding='utf-8-sig')
    # entities.csv 列: PMID, Entity, Type
    lit_nodes = df_entities[['Entity', 'Type']].drop_duplicates().copy()
    lit_nodes.columns = ['id', 'type']
    lit_nodes['name'] = lit_nodes['id']
    print(f"   文献实体节点数: {len(lit_nodes)}")

    print("2. 加载论文节点...")
    df_papers = pd.read_csv(PAPERS_CSV, encoding='utf-8-sig')
    paper_nodes = pd.DataFrame({
        'id': df_papers['PMID'].astype(str),
        'type': 'Paper',
        'name': df_papers['PMID'].astype(str)
    }).drop_duplicates()
    print(f"   论文节点数: {len(paper_nodes)}")

    # 合并基础节点
    all_nodes = pd.concat([lit_nodes, paper_nodes], ignore_index=True)

    # 3. 尝试加载模拟网络（如果存在）
    use_mock = False
    if MOCK_HI_CSV.exists() and MOCK_IT_CSV.exists():
        use_mock = True
        print("3. 加载模拟网络...")
        df_hi = pd.read_csv(MOCK_HI_CSV, encoding='utf-8-sig')
        df_it = pd.read_csv(MOCK_IT_CSV, encoding='utf-8-sig')

        # 模拟网络节点（herb, ingredient, target）
        herbs = set(df_hi['herb'])
        ingredients = set(df_hi['ingredient']).union(set(df_it['ingredient']))
        targets = set(df_it['target'])

        mock_nodes = []
        for h in herbs:
            mock_nodes.append({'id': h, 'type': 'Herb', 'name': h})
        for i in ingredients:
            mock_nodes.append({'id': i, 'type': 'Ingredient', 'name': i})
        for t in targets:
            mock_nodes.append({'id': t, 'type': 'Target', 'name': t})
        mock_nodes_df = pd.DataFrame(mock_nodes).drop_duplicates(subset=['id'])
        print(f"   模拟网络新增节点数: {len(mock_nodes_df)}")

        # 合并节点
        all_nodes = pd.concat([all_nodes, mock_nodes_df], ignore_index=True)
        print(f"   合并后总节点数（去重前）: {len(all_nodes)}")
        all_nodes = all_nodes.drop_duplicates(subset=['id'])
        print(f"   去重后总节点数: {len(all_nodes)}")

        # 生成模拟关系
        relations = []

        # Paper -> Entity (MENTIONS)
        for _, row in df_entities.iterrows():
            relations.append({
                'source': str(row['PMID']),
                'source_type': 'Paper',
                'target': row['Entity'],
                'target_type': row['Type'],
                'relation': 'MENTIONS'
            })
        print(f"   生成 MENTIONS 关系: {len(relations)}")

        # Herb -> Ingredient
        for _, row in df_hi.iterrows():
            relations.append({
                'source': row['herb'],
                'source_type': 'Herb',
                'target': row['ingredient'],
                'target_type': 'Ingredient',
                'relation': 'CONTAINS_INGREDIENT'
            })
        # Ingredient -> Target
        for _, row in df_it.iterrows():
            relations.append({
                'source': row['ingredient'],
                'source_type': 'Ingredient',
                'target': row['target'],
                'target_type': 'Target',
                'relation': 'ACTS_ON'
            })
        print(f"   生成模拟网络关系: {len(df_hi) + len(df_it)}")
    else:
        print("3. 未找到模拟网络文件，仅使用文献实体和论文节点。")
        # 仅生成 MENTIONS 关系
        relations = []
        for _, row in df_entities.iterrows():
            relations.append({
                'source': str(row['PMID']),
                'source_type': 'Paper',
                'target': row['Entity'],
                'target_type': row['Type'],
                'relation': 'MENTIONS'
            })

    # 保存
    print("4. 保存节点和关系文件...")
    all_nodes.to_csv(OUTPUT_NODES, index=False, encoding='utf-8-sig')
    pd.DataFrame(relations).to_csv(OUTPUT_RELATIONS, index=False, encoding='utf-8-sig')

    print(f"   节点文件: {OUTPUT_NODES} ({len(all_nodes)} 个节点)")
    print(f"   关系文件: {OUTPUT_RELATIONS} ({len(relations)} 条关系)")
    print("\n节点类型分布:")
    print(all_nodes['type'].value_counts())

if __name__ == "__main__":
    main()