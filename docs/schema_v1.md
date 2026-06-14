# 中医药干预抑郁症知识图谱 Schema V2

## 实体类型（Entity Types）

| 实体类型 | 英文名称 | 说明 | 示例 |
|----------|----------|------|------|
| 疾病 | Disease | 抑郁症及相关共病 | 抑郁症、焦虑症 |
| 证型 | TcmSyndrome | 中医证候（辨证核心） | 肝郁气滞证、肝郁脾虚证、心脾两虚证 |
| 症状 | Symptom | 临床表现 | 失眠、情绪低落、胸胁胀痛 |
| 方剂 | Formula | 中药复方 | 逍遥散、柴胡疏肝散 |
| 中药 | Herb | 单味中药 | 柴胡、甘草、酸枣仁 |
| 成分 | Ingredient | 具体化合物或活性成分（非化学类别） | 槲皮素、柴胡皂苷A、黄芩素 |
| 靶点 | Target | 分子靶点（蛋白/基因等） | BDNF、5-HT2A、SLC6A4 |
| 通路 | Pathway | 信号通路 | MAPK、PI3K-Akt、cAMP |
| 疗效指标 | Outcome | 临床或实验评估使用的结局指标 | HAMD评分、BDI评分、脑5-HT含量 |
| 不良反应 | AdverseEvent | 不良事件或副作用 | 胃肠道反应、肝损伤 |
| 文献 | Paper | PubMed等来源文献 | PMID: 12345678 |

## 实体属性（部分核心属性）

| 实体类型 | 属性名称 | 说明 | 示例 |
|----------|----------|------|------|
| Herb | name_cn | 中文名 | 柴胡 |
| | name_latin | 拉丁学名 | Bupleurum chinense |
| | property | 性味归经（暂存，后续可独立为实体） | 性微寒、味苦、归肝经 |
| Ingredient | name | 成分名称 | 槲皮素 |
| | cas_number | CAS编号 | 117-39-5 |
| | smiles | 分子SMILES表示 | C1=CC(=CC2=C1C(=O)C3=C(O2)C=C(C=C3O)O)O |
| Paper | title | 文献标题 | Antidepressant effects of Xiaoyao San... |
| | pmid | PubMed ID | 12345678 |
| | year | 发表年份 | 2023 |

## 关系类型（Relation Types）

| 关系名称 | 含义 | 示例三元组 |
|----------|------|------------|
| TREATS | 方剂治疗疾病 | 逍遥散 --TREATS--> 抑郁症 |
| HAS_SYNDROME | 疾病可表现为某证型 | 抑郁症 --HAS_SYNDROME--> 肝郁气滞证 |
| TREATS_SYNDROME | 方剂适用于某证型 | 逍遥散 --TREATS_SYNDROME--> 肝郁脾虚证 |
| HAS_SYMPTOM | 疾病或证型表现出某症状 | 抑郁症 --HAS_SYMPTOM--> 失眠 |
| | | 肝郁脾虚证 --HAS_SYMPTOM--> 胸胁胀痛 |
| CONTAINS_HERB | 方剂包含中药 | 逍遥散 --CONTAINS_HERB--> 柴胡 |
| CONTAINS_INGREDIENT | 中药包含具体成分 | 柴胡 --CONTAINS_INGREDIENT--> 柴胡皂苷A |
| TARGETS | 成分作用于分子靶点 | 槲皮素 --TARGETS--> BDNF |
| INVOLVES_PATHWAY | 靶点参与信号通路 | BDNF --INVOLVES_PATHWAY--> MAPK |
| IMPROVES | 方剂改善某疗效指标 | 逍遥散 --IMPROVES--> HAMD评分 |
| CAUSES_ADVERSE | 方剂/中药/成分引起不良反应 | 柴胡 --CAUSES_ADVERSE--> 胃肠道反应 |
| | | 马兜铃酸 --CAUSES_ADVERSE--> 肾毒性 |
| MENTIONS | 文献提及某实体 | PMID:123 --MENTIONS--> 逍遥散 |
| STUDIES | 文献以某实体为主要研究对象 | PMID:456 --STUDIES--> 抑郁症 |

## 合法关系定义

Disease --HAS_SYNDROME--> TcmSyndrome
Disease --HAS_SYMPTOM--> Symptom

TcmSyndrome --HAS_SYMPTOM--> Symptom

Formula --TREATS--> Disease
Formula --TREATS_SYNDROME--> TcmSyndrome
Formula --IMPROVES--> Outcome
Formula --CONTAINS_HERB--> Herb
Formula --CAUSES_ADVERSE--> AdverseEvent

Herb --CONTAINS_INGREDIENT--> Ingredient
Herb --CAUSES_ADVERSE--> AdverseEvent

Ingredient --TARGETS--> Target
Ingredient --CAUSES_ADVERSE--> AdverseEvent

Target --INVOLVES_PATHWAY--> Pathway

Paper --MENTIONS--> (Disease | TcmSyndrome | Symptom | Formula | Herb | Ingredient | Target | Pathway | Outcome | AdverseEvent)
Paper --STUDIES--> (Disease | Formula | Herb | Ingredient)
## 示例三元组
抑郁症 --HAS_SYNDROME--> 肝郁气滞证
抑郁症 --HAS_SYNDROME--> 肝郁脾虚证
抑郁症 --HAS_SYMPTOM--> 失眠
肝郁脾虚证 --HAS_SYMPTOM--> 情绪抑郁
肝郁脾虚证 --HAS_SYMPTOM--> 胸胁胀痛
逍遥散 --TREATS--> 抑郁症
逍遥散 --TREATS_SYNDROME--> 肝郁脾虚证
逍遥散 --IMPROVES--> HAMD评分
逍遥散 --CONTAINS_HERB--> 柴胡
逍遥散 --CONTAINS_HERB--> 白芍
柴胡 --CONTAINS_INGREDIENT--> 柴胡皂苷A
柴胡皂苷A --TARGETS--> BDNF
BDNF --INVOLVES_PATHWAY--> MAPK
柴胡疏肝散 --CAUSES_ADVERSE--> 胃肠道反应
马兜铃酸 --CAUSES_ADVERSE--> 肾毒性
PMID: 12345678 --MENTIONS--> 抑郁症
PMID: 12345678 --MENTIONS--> 逍遥散
PMID: 12345678 --MENTIONS--> BDNF
PMID: 23456789 --STUDIES--> 逍遥散
PMID: 23456789 --STUDIES--> 抑郁症