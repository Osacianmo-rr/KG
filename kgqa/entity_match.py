from neo4j_client import client

def extract_entity_fuzzy(question: str, label_filter: list[str] = None):
    """
    从问题中提取实体，精确优先，忽略大小写。
    返回 (entity_name, labels) 或 (None, [])
    """
    words = [w.strip().rstrip('.,?!') for w in question.split() if len(w.strip()) > 2]
    candidates = []
    for i in range(len(words)):
        candidates.append(words[i])
        if i+1 < len(words):
            candidates.append(words[i] + " " + words[i+1])
        if i+2 < len(words):
            candidates.append(words[i] + " " + words[i+1] + " " + words[i+2])
    candidates = sorted(set(candidates), key=lambda x: -len(x))

    label_clause = ""
    if label_filter:
        labels_or = " OR ".join([f"n:{lbl}" for lbl in label_filter])
        label_clause = f" AND ({labels_or})"

    # 第一轮：精确匹配（不区分大小写）
    for candidate in candidates:
        query = f"""
        MATCH (n)
        WHERE n.name IS NOT NULL{label_clause} AND toLower(n.name) = toLower($candidate)
        RETURN n.name AS name, labels(n) AS labels
        LIMIT 1
        """
        with client.driver.session() as session:
            result = session.run(query, {"candidate": candidate})
            for record in result:
                node_labels = record.get("labels", [])
                if label_filter is None or any(lbl in label_filter for lbl in node_labels):
                    return record["name"], node_labels

    # 第二轮：模糊匹配（不区分大小写）
    for candidate in candidates:
        query = f"""
        MATCH (n)
        WHERE n.name IS NOT NULL{label_clause} AND toLower(n.name) CONTAINS toLower($candidate)
        RETURN n.name AS name, labels(n) AS labels
        LIMIT 1
        """
        with client.driver.session() as session:
            result = session.run(query, {"candidate": candidate})
            for record in result:
                node_labels = record.get("labels", [])
                if label_filter is None or any(lbl in label_filter for lbl in node_labels):
                    return record["name"], node_labels

    return None, []