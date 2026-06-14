# 1. 草药 → 成分
def herb_ingredient(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[:CONTAINS_INGREDIENT]->(i:Ingredient)
    RETURN DISTINCT i.name AS result
    """
    return query, {"name": name}

# 2. 草药 → 靶点
def herb_target(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[:TARGETS]->(t:Target)
    RETURN DISTINCT t.name AS result
    """
    return query, {"name": name}

# 3. 草药 → 功效
def herb_efficacy(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[:HAS_EFFICACY]->(e:Efficacy)
    RETURN DISTINCT e.name AS result
    """
    return query, {"name": name}

# 4. 草药配伍（对称关系）
def pair_with(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[:PAIRS_WITH]-(h2:Herb)
    RETURN DISTINCT h2.name AS result
    """
    return query, {"name": name}

# 5. 证据提及疾病 / 靶点
def evidence_mentions_disease(name: str):
    query = """
    MATCH (p:Paper)-[:MENTIONS]->(d:Disease {name: $name})
    RETURN DISTINCT p.name AS result
    """
    return query, {"name": name}

def evidence_mentions_target(name: str):
    query = """
    MATCH (p:Paper)-[:MENTIONS]->(t:Target {name: $name})
    RETURN DISTINCT p.name AS result
    """
    return query, {"name": name}