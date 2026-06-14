# neo4j_client.py

from neo4j import GraphDatabase

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def run_query(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record["result"] for record in result]

    def run_graph_query(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            nodes = {}
            edges = []
            for record in result:
                n = record.get("n")
                m = record.get("m")
                rel_type = record.get("rel_type")  # 关系类型字符串

                if n:
                    n_id = n.element_id  # 或 str(n.id) 若 Neo4j 4.x
                    if n_id not in nodes:
                        nodes[n_id] = {
                            "id": n_id,
                            "label": n.get("name", str(n_id)),
                            "group": list(n.labels)[0] if n.labels else "Unknown"
                        }
                if m:
                    m_id = m.element_id
                    if m_id not in nodes:
                        nodes[m_id] = {
                            "id": m_id,
                            "label": m.get("name", str(m_id)),
                            "group": list(m.labels)[0] if m.labels else "Unknown"
                        }
                if n and m and rel_type:
                    edges.append({
                        "from": n.element_id,
                        "to": m.element_id,
                        "label": rel_type
                    })
            # 对边去重（因为数据可能重复）
            unique_edges = []
            seen = set()
            for e in edges:
                key = (e["from"], e["to"], e["label"])
                if key not in seen:
                    seen.add(key)
                    unique_edges.append(e)
            return {"nodes": list(nodes.values()), "edges": unique_edges}
# 确保下面的连接信息正确
client = Neo4jClient(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="neo4j123456"
)