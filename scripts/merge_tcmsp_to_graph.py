#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 TCMSP 外部数据（herb-ingredient, ingredient-target）与已有文献实体合并
输出:
  - data/processed/final_nodes.csv   (所有节点：文献实体 + 外部成分、靶点)
  - data/processed/final_relations.csv (所有关系：文献内关系 + 外部关系)
"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"

# 1. 加载已有文献实体 (entities.csv)
entities_df = pd.read_csv(PROCESSED_DIR / "entities.csv", encoding='utf-8-sig')
# entities_df 列: PMID, Entity, Type
# 去重得到节点 (不区分PMID，只取唯一实体)
existing_nodes = entities_df[['Entity', 'Type']].drop_duplicates().copy()
existing_nodes.rename(columns={'Entity': 'id', 'Type': 'type'}, inplace=True)
print(f"已有实体节点数: {len(existing_nodes)}")

# 2. 加载论文节点 (从 high_quality_corpus.csv 中提取 PMID)
papers_df = pd.read_csv(PROCESSED_DIR / "high_quality_corpus.csv", encoding='utf-8-sig')
paper_nodes = pd.DataFrame({
    'id': papers_df['PMID'].astype(str),
    'type': 'Paper'
})
print(f"论文节点数: {len(paper_nodes)}")

# 3. 加载 TCMSP 外部数据
herb_ing = pd.read_csv(EXTERNAL_DIR / "tcmsp_herb_ingredient.csv")
ing_target = pd.read_csv(EXTERNAL_DIR / "tcmsp_ingredient_target.csv")

# 从外部数据中提取新节点（成分、靶点）
ingredients = set(herb_ing['ingredient']) | set(ing_target['ingredient'])
targets = set(ing_target['target'])

# 注意：已有实体中可能已经包含部分成分或靶点（从文献抽取的），我们需要去重
all_ing_nodes = pd.DataFrame({'id': list(ingredients), 'type': 'Ingredient'})
all_target_nodes = pd.DataFrame({'id': list(targets), 'type': 'Target'})

# 合并所有节点：已有实体节点 + 论文节点 + 成分节点 + 靶点节点
nodes = pd.concat([existing_nodes, paper_nodes, all_ing_nodes, all_target_nodes], ignore_index=True)
nodes = nodes.drop_duplicates(subset=['id', 'type'])
print(f"合并后总节点数: {len(nodes)}")
nodes.to_csv(PROCESSED_DIR / "final_nodes.csv", index=False, encoding='utf-8-sig')

# 4. 构建关系
# 4.1 已有关系：从 entities.csv 生成 Paper -> Entity (MENTIONS)
# 每篇文献中的每个实体生成一条关系
paper_mentions = entities_df[['PMID', 'Entity', 'Type']].copy()
paper_mentions.rename(columns={'PMID': 'source', 'Entity': 'target'}, inplace=True)
paper_mentions['source_type'] = 'Paper'
paper_mentions['target_type'] = paper_mentions['Type']
paper_mentions['relation'] = 'MENTIONS'
paper_mentions = paper_mentions[['source', 'source_type', 'relation', 'target', 'target_type']]

# 4.2 实体间已有关系（如果之前生成了 relations.csv，可以加载；这里重新生成共现关系）
# 为了简化，我们直接基于 entities.csv 生成同一篇文献中实体对之间的预定义关系
# 定义关系类型映射
RELATION_MAP = {
    ('Formula', 'Disease'): 'TREATS',
    ('Formula', 'Herb'): 'CONTAINS_HERB',
    ('Herb', 'Ingredient'): 'CONTAINS_INGREDIENT',
    ('Ingredient', 'Target'): 'ACTS_ON',
    ('Target', 'Pathway'): 'INVOLVED_IN',
    ('Syndrome', 'Disease'): 'ASSOCIATED_WITH',
    ('Formula', 'Symptom'): 'RELIEVES_SYMPTOM',
}
# 按 PMID 分组
grouped = entities_df.groupby('PMID')
cooccur_relations = []
for pmid, group in grouped:
    ents = list(zip(group['Entity'], group['Type']))
    for i, (e1, t1) in enumerate(ents):
        for j, (e2, t2) in enumerate(ents[i+1:], start=i+1):
            # 检查两个方向
            if (t1, t2) in RELATION_MAP:
                cooccur_relations.append({
                    'source': e1,
                    'source_type': t1,
                    'relation': RELATION_MAP[(t1, t2)],
                    'target': e2,
                    'target_type': t2
                })
            elif (t2, t1) in RELATION_MAP:
                cooccur_relations.append({
                    'source': e2,
                    'source_type': t2,
                    'relation': RELATION_MAP[(t2, t1)],
                    'target': e1,
                    'target_type': t1
                })
df_cooccur = pd.DataFrame(cooccur_relations)
print(f"共现关系数: {len(df_cooccur)}")

# 4.3 外部 TCMSP 关系
# herb -> ingredient
herb_ing_rel = herb_ing.rename(columns={'herb': 'source', 'ingredient': 'target'})
herb_ing_rel['source_type'] = 'Herb'
herb_ing_rel['target_type'] = 'Ingredient'
herb_ing_rel['relation'] = 'CONTAINS_INGREDIENT'
# ingredient -> target
ing_target_rel = ing_target.rename(columns={'ingredient': 'source', 'target': 'target'})
ing_target_rel['source_type'] = 'Ingredient'
ing_target_rel['target_type'] = 'Target'
ing_target_rel['relation'] = 'ACTS_ON'

# 合并所有关系
all_relations = pd.concat([
    paper_mentions,
    df_cooccur,
    herb_ing_rel,
    ing_target_rel
], ignore_index=True)
# 去重（可能重复）
all_relations = all_relations.drop_duplicates()
print(f"总关系数: {len(all_relations)}")
all_relations.to_csv(PROCESSED_DIR / "final_relations.csv", index=False, encoding='utf-8-sig')

print("整合完成！")
print(f"最终节点文件: {PROCESSED_DIR / 'final_nodes.csv'}")
print(f"最终关系文件: {PROCESSED_DIR / 'final_relations.csv'}")