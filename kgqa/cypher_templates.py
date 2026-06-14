# cypher_templates.py

# ==================== 文本查询模板 ====================
def herb_ingredient(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[:CONTAINS_INGREDIENT]->(i:Ingredient)
    RETURN DISTINCT i.name AS result
    """
    return query, {"name": name}

def herb_target(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[:TARGETS]->(t:Target)
    RETURN DISTINCT t.name AS result
    """
    return query, {"name": name}

def herb_efficacy(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[:HAS_EFFICACY]->(e:Efficacy)
    RETURN DISTINCT e.name AS result
    """
    return query, {"name": name}

def pair_with(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[:PAIRS_WITH]-(h2:Herb)
    RETURN DISTINCT h2.name AS result
    """
    return query, {"name": name}

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

# ==================== 图形查询模板（返回节点和关系） ====================
def graph_herb_ingredient(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[r:CONTAINS_INGREDIENT]->(i:Ingredient)
    RETURN h AS n, type(r) AS rel_type, i AS m
    """
    return query, {"name": name}

def graph_herb_target(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[r:TARGETS]->(t:Target)
    RETURN h AS n, type(r) AS rel_type, t AS m
    """
    return query, {"name": name}

def graph_herb_efficacy(name: str):
    query = """
    MATCH (h:Herb {name: $name})-[r:HAS_EFFICACY]->(e:Efficacy)
    RETURN h AS n, type(r) AS rel_type, e AS m
    """
    return query, {"name": name}

def graph_pair_with(name: str):
    query = """
    MATCH (h1:Herb {name: $name})-[r:PAIRS_WITH]-(h2:Herb)
    RETURN h1 AS n, type(r) AS rel_type, h2 AS m
    """
    return query, {"name": name}

def graph_evidence_mentions_disease(name: str):
    query = """
    MATCH (p:Paper)-[r:MENTIONS]->(d:Disease)
    WHERE toLower(d.name) = toLower($name)
    RETURN p AS n, type(r) AS rel_type, d AS m
    """
    return query, {"name": name}


def graph_evidence_mentions_target(name: str):
    query = """
    MATCH (p:Paper)-[r:MENTIONS]->(t:Target)
    WHERE toLower(t.name) = toLower($name)
    RETURN p AS n, type(r) AS rel_type, t AS m
    """
    return query, {"name": name}