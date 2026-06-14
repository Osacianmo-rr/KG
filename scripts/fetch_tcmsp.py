#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TCMSP 数据获取脚本
输入: data/dictionaries/herb.txt (你的中药列表)
输出: data/external/tcmsp_herb_ingredient.csv 和 tcmsp_ingredient_target.csv
"""

import requests
import pandas as pd
import time
import random
from pathlib import Path

# =========================
# 基础配置
# =========================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DICT_DIR = PROJECT_ROOT / "data" / "dictionaries"
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"
EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

# 读取你的 herb.txt
herb_file = DICT_DIR / "herb.txt"
with open(herb_file, 'r', encoding='utf-8') as f:
    herbs = [line.strip() for line in f if line.strip()]

print(f"找到 {len(herbs)} 味药材，开始获取数据...")


# =========================
# 路径A: 官方数据下载 (推荐)
# =========================
def download_official_data():
    """从TCMSP官网下载官方关系文件"""
    print("正在从 TCMSP 官网下载官方数据文件...")

    # 官方文件下载链接
    herb_comp_url = "https://tcmsp-e.com/attachment/tcmspDB/23_Herbs_Molecules_Relationships.xlsx"
    comp_target_url = "https://tcmsp-e.com/attachment/tcmspDB/34_Molecules_Targets_Relationships.xlsx"

    try:
        print("下载草药-成分关系文件...")
        df_herb_comp = pd.read_excel(herb_comp_url)
        print("下载成分-靶点关系文件...")
        df_comp_target = pd.read_excel(comp_target_url)

        print("官方数据下载成功，正在解析...")
        return df_herb_comp, df_comp_target
    except Exception as e:
        print(f"官方数据下载失败: {e}")
        return None, None


def parse_official_data(herbs, df_herb_comp, df_comp_target):
    """从官方数据中筛选出你的药材"""
    # 标准化药材名称（小写）
    herbs_lower = [h.lower() for h in herbs]

    # 筛选草药-成分关系
    herb_comp_filtered = df_herb_comp[df_herb_comp['herb_name'].str.lower().isin(herbs_lower)]
    herb_comp_result = herb_comp_filtered[['herb_name', 'molecule_name']]

    # 获取筛选出的成分列表
    molecules = herb_comp_filtered['molecule_name'].unique()

    # 筛选成分-靶点关系
    comp_target_filtered = df_comp_target[df_comp_target['molecule_name'].isin(molecules)]
    comp_target_result = comp_target_filtered[['molecule_name', 'target_name']]

    return herb_comp_result, comp_target_result


# =========================
# 路径B: 模拟数据 (备选方案)
# =========================
def generate_mock_data(herbs):
    """生成模拟数据（仅供流程测试）"""
    print("生成模拟数据...")
    import random
    random.seed(42)

    herb_ing = []
    ing_target = []
    all_ingredients = []

    for herb in herbs:
        num_ing = random.randint(5, 15)
        herb_ingredients = []
        for _ in range(num_ing):
            ing = f"{herb.replace(' ', '_')}_ing_{random.randint(1, 100)}"
            herb_ing.append((herb, ing))
            herb_ingredients.append(ing)
            all_ingredients.append(ing)

            num_tar = random.randint(3, 12)
            for __ in range(num_tar):
                tar = f"TAR_{random.randint(1, 500)}"
                ing_target.append((ing, tar))

    return herb_ing, ing_target, all_ingredients


# =========================
# 主函数
# =========================
def main():
    # 尝试路径A
    df_herb_comp, df_comp_target = download_official_data()

    if df_herb_comp is not None and df_comp_target is not None:
        print("正在解析官方数据...")
        herb_ing, ing_target = parse_official_data(herbs, df_herb_comp, df_comp_target)

        # 保存结果
        herb_ing.to_csv(EXTERNAL_DIR / "tcmsp_herb_ingredient.csv", index=False)
        ing_target.to_csv(EXTERNAL_DIR / "tcmsp_ingredient_target.csv", index=False)

        print(f"官方数据解析完成！")
        print(f"  - 草药-成分关系: {len(herb_ing)} 条")
        print(f"  - 成分-靶点关系: {len(ing_target)} 条")

    else:
        # 路径B：生成模拟数据
        print("使用模拟数据作为备选方案...")
        herb_ing, ing_target, ingredients = generate_mock_data(herbs)

        # 转换为DataFrame并保存
        df_hi = pd.DataFrame(herb_ing, columns=['herb', 'ingredient'])
        df_it = pd.DataFrame(ing_target, columns=['ingredient', 'target'])

        df_hi.to_csv(EXTERNAL_DIR / "tcmsp_herb_ingredient.csv", index=False)
        df_it.to_csv(EXTERNAL_DIR / "tcmsp_ingredient_target.csv", index=False)

        print(f"模拟数据生成完成！")
        print(f"  - 草药-成分关系: {len(df_hi)} 条")
        print(f"  - 成分-靶点关系: {len(df_it)} 条")

    print(f"\n数据文件已保存至: {EXTERNAL_DIR}")
    print("现在你可以使用这些数据来扩充你的知识图谱了。")


if __name__ == "__main__":
    main()