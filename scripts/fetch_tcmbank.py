import requests
import pandas as pd
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"
EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

# === 目标实体：你的 herb.txt 中的草药 ===
herb_file = PROJECT_ROOT / "data" / "dictionaries" / "herb.txt"
with open(herb_file, 'r', encoding='utf-8') as f:
    target_herbs = [line.strip() for line in f if line.strip()]

# TCMBank API 地址 (根据实际情况调整)
API_BASE = "https://tcmbank.cn/api/herb"

all_herb_data = []

for herb in target_herbs[:20]:  # 先测试一部分，防止封 IP
    try:
        response = requests.get(f"{API_BASE}/{herb}", timeout=10)
        if response.status_code == 200:
            data = response.json()

            # 提取草药基本信息
            herb_info = {
                "herb_name": herb,
                "ingredients": ", ".join(data.get("ingredients", [])),
                "targets": ", ".join(data.get("targets", [])),
                "diseases": ", ".join(data.get("diseases", [])),
            }
            all_herb_data.append(herb_info)

            # 进一步展开 ingredient -> target 对应关系
            for ing in data.get("ingredients", []):
                # 这里可以继续深度查询每个成分对应的靶点
                pass
        else:
            print(f"{herb} 请求失败: {response.status_code}")
        time.sleep(1)  # 礼貌限速
    except Exception as e:
        print(f"{herb} 出错: {e}")

# 保存结果为 CSV 文件
df = pd.DataFrame(all_herb_data)
df.to_csv(EXTERNAL_DIR / "tcmbank_herb_data.csv", index=False, encoding='utf-8-sig')
print(f"数据已保存至 {EXTERNAL_DIR / 'tcmbank_herb_data.csv'}")
print(f"共获取 {len(df)} 条草药信息")

print("\nTCMBank 原始 API 返回字段示例：")
print(data.keys() if 'data' in locals() else "暂无示例数据")