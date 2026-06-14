from neo4j import GraphDatabase

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def run_query(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record["result"] for record in result]

# 全局实例，请改成你自己的连接信息
client = Neo4jClient(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="neo4j123456"
)