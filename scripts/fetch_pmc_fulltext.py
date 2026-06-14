# scripts/fetch_pmc_fulltext.py

import time
import pandas as pd
from pathlib import Path
from Bio import Entrez

# 设置你的邮箱（NCBI 要求）
Entrez.email = "osacianmo@163.com"   # 请修改为真实邮箱

# 项目路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
CORPUS_FILE = DATA_RAW / "pubmed_tcm_depression_v2.csv"   # 你的347篇文献文件
OUTPUT_DIR = PROJECT_ROOT / "data" / "pmc_articles"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def pmid_to_pmcid(pmid):
    """使用 Entrez 将 PMID 转换为 PMCID"""
    try:
        handle = Entrez.esearch(db="pmc", term=pmid, retmode="xml")
        record = Entrez.read(handle)
        handle.close()
        idlist = record.get("IdList", [])
        if idlist:
            return idlist[0]   # 返回第一个 PMCID
        else:
            return None
    except Exception as e:
        print(f"转换 PMID {pmid} 时出错: {e}")
        return None

def main():
    print("正在加载文献列表...")
    df = pd.read_csv(CORPUS_FILE, encoding='utf-8-sig')
    pmids = df['PMID'].astype(str).tolist()
    print(f"共 {len(pmids)} 篇文献")

    # 分批转换，避免请求过快
    pmc_ids = []
    for i, pmid in enumerate(pmids):
        print(f"处理 {i+1}/{len(pmids)}: PMID={pmid}")
        pmcid = pmid_to_pmcid(pmid)
        if pmcid:
            pmc_ids.append(pmcid)
            print(f"  -> PMCID: {pmcid}")
        else:
            print(f"  -> 未找到 PMCID")
        time.sleep(0.5)   # 礼貌延迟

    print(f"\n成功转换 {len(pmc_ids)} 个 PMCID")
    # 保存 PMCID 列表供后续使用
    with open(OUTPUT_DIR / "pmc_ids.txt", "w", encoding="utf-8") as f:
        for pid in pmc_ids:
            f.write(pid + "\n")
    print(f"PMCID 列表已保存至 {OUTPUT_DIR / 'pmc_ids.txt'}")

if __name__ == "__main__":
    main()