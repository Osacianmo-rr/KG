import requests
from pathlib import Path
from Bio import Entrez
import pandas as pd
import json

# ========== 配置 NCBI 邮箱==========
Entrez.email = "osacianmo@163.com"


def search_pubmed(query, retmax=100):
    """
    根据检索词获取PMID列表
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    pmid_list = data["esearchresult"]["idlist"]
    return pmid_list


def save_pmids(pmid_list):
    """
    保存PMID到文件
    """
    output_dir = Path("../data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "pmid_list.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for pmid in pmid_list:
            f.write(pmid + "\n")
    print(f"PMID已保存：{output_file}")


def fetch_pubmed_details(pmid_list):
    """
    获取文献详细信息（标题、摘要、期刊、年份、作者）
    """
    handle = Entrez.efetch(
        db="pubmed",
        id=",".join(pmid_list),
        rettype="medline",
        retmode="xml"
    )
    records = Entrez.read(handle)
    papers = []
    for article in records["PubmedArticle"]:
        try:
            medline = article["MedlineCitation"]
            article_info = medline["Article"]
            pmid = str(medline["PMID"])
            title = str(article_info.get("ArticleTitle", ""))
            abstract = ""
            if "Abstract" in article_info:
                abstract_parts = article_info["Abstract"].get("AbstractText", [])
                abstract = " ".join([str(x) for x in abstract_parts])
            journal = ""
            if "Journal" in article_info:
                journal = str(article_info["Journal"]["Title"])
            year = ""
            try:
                year = article_info["Journal"]["JournalIssue"]["PubDate"]["Year"]
            except:
                pass
            authors = []
            if "AuthorList" in article_info:
                for author in article_info["AuthorList"]:
                    lastname = author.get("LastName", "")
                    firstname = author.get("ForeName", "")
                    full_name = (lastname + " " + firstname).strip()
                    if full_name:
                        authors.append(full_name)
            papers.append({
                "PMID": pmid,
                "Title": title,
                "Abstract": abstract,
                "Journal": journal,
                "Year": year,
                "Authors": "; ".join(authors)
            })
        except Exception as e:
            print("解析失败：", e)
    return papers


def save_papers(papers):
    """
    保存文献详细信息为 JSON 和 CSV
    """
    output_dir = Path("../data/raw")
    json_file = output_dir / "pubmed_100.json"
    csv_file = output_dir / "pubmed_100.csv"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    df = pd.DataFrame(papers)
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    print(f"文献详情已保存至：{json_file} 和 {csv_file}")


if __name__ == "__main__":
    query = "depression AND traditional chinese medicine"
    print("开始检索PubMed...")
    pmid_list = search_pubmed(query, retmax=100)
    print(f"检索到 {len(pmid_list)} 篇文献")
    print("\n前10个PMID：")
    for pmid in pmid_list[:10]:
        print(pmid)

    save_pmids(pmid_list)

    print("\n开始获取文献详细信息...")
    papers = fetch_pubmed_details(pmid_list)
    print(f"成功获取 {len(papers)} 篇文献")
    save_papers(papers)

    print("\n完成")