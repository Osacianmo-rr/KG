from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from qa_rules import classify_question
from entity_match import extract_entity_fuzzy   # 新模糊匹配
from cypher_templates import (
    herb_ingredient, herb_target, herb_efficacy, pair_with,
    evidence_mentions_disease, evidence_mentions_target,
    graph_herb_ingredient, graph_herb_target, graph_herb_efficacy,
    graph_pair_with, graph_evidence_mentions_disease, graph_evidence_mentions_target
)
from neo4j_client import client

app = FastAPI()

# 挂载静态文件（必须在路由之前）
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/qa")
def qa(q: str):
    qtype = classify_question(q)
    if qtype == "unknown":
        return {"answer": "Question type not supported."}

    entity = None
    entity_type = None

    if qtype == "herb_ingredient":
        entity, labels = extract_entity_fuzzy(q, label_filter=["Herb"])
        if not entity:
            return {"answer": "Herb not found in question."}
        entity_type = "Herb"
        cypher, params = herb_ingredient(entity)

    elif qtype == "herb_target":
        entity, labels = extract_entity_fuzzy(q, label_filter=["Herb"])
        if not entity:
            return {"answer": "Herb not found."}
        entity_type = "Herb"
        cypher, params = herb_target(entity)

    elif qtype == "herb_efficacy":
        entity, labels = extract_entity_fuzzy(q, label_filter=["Herb"])
        if not entity:
            return {"answer": "Herb not found."}
        entity_type = "Herb"
        cypher, params = herb_efficacy(entity)

    elif qtype == "pair_with":
        entity, labels = extract_entity_fuzzy(q, label_filter=["Herb"])
        if not entity:
            return {"answer": "Herb not found."}
        entity_type = "Herb"
        cypher, params = pair_with(entity)

    elif qtype == "evidence_mentions":
        # 同时支持疾病和靶点，优先返回匹配度最高的
        entity, ent_labels = extract_entity_fuzzy(q, label_filter=["Disease", "Target"])
        if not entity:
            return {"answer": "Entity not found for evidence query."}
        if "Disease" in ent_labels:
            entity_type = "Disease"
            cypher, params = evidence_mentions_disease(entity)
        elif "Target" in ent_labels:
            entity_type = "Target"
            cypher, params = evidence_mentions_target(entity)
        else:
            return {"answer": "Unsupported entity type for evidence."}
    else:
        return {"answer": "Question type not supported."}

    rows = client.run_query(cypher, params)
    return {
        "question": q,
        "type": qtype,
        "entity": entity,
        "entity_type": entity_type,
        "result": rows
    }

@app.get("/graph")
def get_graph(qtype: str = Query(...), entity: str = Query(...), entity_type: str = "Herb"):
    """
    根据问题类型和实体返回子图数据（用于前端可视化）
    """
    if qtype == "herb_ingredient":
        cypher, params = graph_herb_ingredient(entity)
    elif qtype == "herb_target":
        cypher, params = graph_herb_target(entity)
    elif qtype == "herb_efficacy":
        cypher, params = graph_herb_efficacy(entity)
    elif qtype == "pair_with":
        cypher, params = graph_pair_with(entity)
    elif qtype == "evidence_mentions":
        if entity_type == "Disease":
            cypher, params = graph_evidence_mentions_disease(entity)
        elif entity_type == "Target":
            cypher, params = graph_evidence_mentions_target(entity)
        else:
            return {"nodes": [], "edges": []}
    else:
        return {"nodes": [], "edges": []}

    graph_data = client.run_graph_query(cypher, params)
    return graph_data


# 用于评测脚本直接调用的函数
def answer(question: str):
    """可供外部调用的问答函数，返回结果列表"""
    qtype = classify_question(question)
    if qtype == "unknown":
        return []

    if qtype == "herb_ingredient":
        entity, labels = extract_entity_fuzzy(question, label_filter=["Herb"])
        if not entity:
            return []
        cypher, params = herb_ingredient(entity)

    elif qtype == "herb_target":
        entity, labels = extract_entity_fuzzy(question, label_filter=["Herb"])
        if not entity:
            return []
        cypher, params = herb_target(entity)

    elif qtype == "herb_efficacy":
        entity, labels = extract_entity_fuzzy(question, label_filter=["Herb"])
        if not entity:
            return []
        cypher, params = herb_efficacy(entity)

    elif qtype == "pair_with":
        entity, labels = extract_entity_fuzzy(question, label_filter=["Herb"])
        if not entity:
            return []
        cypher, params = pair_with(entity)

    elif qtype == "evidence_mentions":
        entity, ent_labels = extract_entity_fuzzy(question, label_filter=["Disease", "Target"])
        if not entity:
            return []
        if "Disease" in ent_labels:
            cypher, params = evidence_mentions_disease(entity)
        elif "Target" in ent_labels:
            cypher, params = evidence_mentions_target(entity)
        else:
            return []
    else:
        return []

    rows = client.run_query(cypher, params)
    return rows