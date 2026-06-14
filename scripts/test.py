import pandas as pd
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "neo4j123456"  # 替换为实际密码

# 读取 Dryad 文件，获取映射
df = pd.read_csv("data/tcmsp/Herb_target.csv", encoding='utf-8-sig')
# 检查列名，如果不同请修改
herb_id_col = 'Herb ID'
latin_name_col = 'Latin_name'
mapping = dict(zip(df[herb_id_col].astype(str), df[latin_name_col]))

driver = GraphDatabase.driver(uri, auth=(user, password))

def update_name(tx, hid, latin):
    tx.run("MATCH (n:Node {type:'Herb', id: $hid}) SET n.name = $latin", hid=hid, latin=latin)

with driver.session() as session:
    for hid, latin in mapping.items():
        if pd.notna(latin):
            session.execute_write(update_name, hid, latin)
            print(f"Updated {hid} -> {latin}")

driver.close()