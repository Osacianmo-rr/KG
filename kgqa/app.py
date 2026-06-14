from fastapi import FastAPI
from qa_rules import classify_question
from entity_match import extract_entity
from cypher_templates import *
from neo4j_client import client

app = FastAPI()

# 预置实体列表（后续可动态加载）
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

TARGETS = ["AKT1", "ALOX5", "TNF", "MTOR"]  # 可扩展

@app.get("/qa")
def qa(q: str):
    qtype = classify_question(q)

    if qtype == "herb_ingredient":
        entity = extract_entity(q, HERBS)
        if not entity:
            return {"answer": "Herb not found in question."}
        cypher, params = herb_ingredient(entity)

    elif qtype == "herb_target":
        entity = extract_entity(q, HERBS)
        if not entity:
            return {"answer": "Herb not found."}
        cypher, params = herb_target(entity)

    elif qtype == "herb_efficacy":
        entity = extract_entity(q, HERBS)
        if not entity:
            return {"answer": "Herb not found."}
        cypher, params = herb_efficacy(entity)

    elif qtype == "pair_with":
        entity = extract_entity(q, HERBS)
        if not entity:
            return {"answer": "Herb not found."}
        cypher, params = pair_with(entity)

    elif qtype == "evidence_mentions":
        # 先尝试匹配疾病，再尝试靶点
        entity = extract_entity(q, DISEASES)
        if entity:
            cypher, params = evidence_mentions_disease(entity)
        else:
            entity = extract_entity(q, TARGETS)
            if entity:
                cypher, params = evidence_mentions_target(entity)
            else:
                return {"answer": "Entity not supported for evidence query."}
    else:
        return {"answer": "Question type not supported."}

    # 执行查询
    rows = client.run_query(cypher, params)
    return {
        "question": q,
        "type": qtype,
        "entity": entity if 'entity' in locals() else None,
        "result": rows
    }