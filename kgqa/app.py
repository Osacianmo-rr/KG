from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from qa_rules import classify_question
from entity_match import extract_entity
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

# 实体列表（用于证据提及的判断）
HERBS = [
    "Bletilla striata", "Siegesbeckia orientalis", "Triticum aestivum",
    "Radix et rhizoma rhodiolae", "Magnolia liliflora", "Melia toosendan",
    "Coptis chinensis", "Paeonia obovata", "Curcuma aromatica",
    "Scutellaria baicalensis", "Phellodendron amurense", "Gardenia jasminoides",
    "Commelina communis", "Andrographis paniculata", "Picrorhiza kurrooa",
    "Salvia miltiorrhiza"
]

DISEASES = [
    "depression", "major depressive disorder",
    "post-stroke depression", "postpartum depression"
]

TARGETS = ["AKT1", "ALOX5", "TNF", "MTOR"]  # 可按需扩展

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
        entity = extract_entity(q, HERBS)
        if not entity:
            return {"answer": "Herb not found in question."}
        entity_type = "Herb"
        cypher, params = herb_ingredient(entity)

    elif qtype == "herb_target":
        entity = extract_entity(q, HERBS)
        if not entity:
            return {"answer": "Herb not found."}
        entity_type = "Herb"
        cypher, params = herb_target(entity)

    elif qtype == "herb_efficacy":
        entity = extract_entity(q, HERBS)
        if not entity:
            return {"answer": "Herb not found."}
        entity_type = "Herb"
        cypher, params = herb_efficacy(entity)

    elif qtype == "pair_with":
        entity = extract_entity(q, HERBS)
        if not entity:
            return {"answer": "Herb not found."}
        entity_type = "Herb"
        cypher, params = pair_with(entity)

    elif qtype == "evidence_mentions":
        # 先尝试匹配疾病
        entity = extract_entity(q, DISEASES)
        if entity:
            entity_type = "Disease"
            cypher, params = evidence_mentions_disease(entity)
        else:
            # 再尝试匹配靶点
            entity = extract_entity(q, TARGETS)
            if entity:
                entity_type = "Target"
                cypher, params = evidence_mentions_target(entity)
            else:
                return {"answer": "Entity not found for evidence query."}
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