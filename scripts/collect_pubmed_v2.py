# scripts/collect_pubmed_v2.py

import argparse
import json
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import requests
from Bio import Entrez
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =========================
# 基础配置
# =========================
Entrez.email = "osacianmo@163.com"
Entrez.tool = "TCM_Depression_KnowledgeGraph"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PREFIX = "pubmed_tcm_depression_v2"


# =========================
# 工具函数
# =========================
def build_session() -> requests.Session:
    """
    构建带重试机制的 requests 会话，增强网络稳定性
    """
    session = requests.Session()

    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update(
        {
            "User-Agent": "TCM_Depression_KnowledgeGraph/1.0",
            "Accept": "application/json",
        }
    )
    return session


def clean_text(text: str) -> str:
    """
    清理空白字符
    """
    if text is None:
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_year(pub_date) -> str:
    """
    从 PubDate 中尽量提取年份
    """
    if not pub_date:
        return ""

    year = ""
    try:
        if "Year" in pub_date and pub_date["Year"]:
            year = str(pub_date["Year"])
        elif "MedlineDate" in pub_date and pub_date["MedlineDate"]:
            m = re.search(r"\d{4}", str(pub_date["MedlineDate"]))
            if m:
                year = m.group(0)
    except Exception:
        pass

    return year


# =========================
# 检索式设计
# =========================
def build_query_specs() -> List[Dict]:
    """
    返回检索式配置。
    这些检索式是按“抑郁症 + 中医药干预/方剂/单味药/机制/证型”分组设计的，
    目的是降低噪声并提高后续抽取质量。
    """
    return [
        {
            "label": "core_tcm_intervention",
            "query": (
                '("depression"[tiab] OR "depressive disorder"[tiab] OR '
                '"major depressive disorder"[tiab] OR MDD[tiab]) AND '
                '("traditional chinese medicine"[tiab] OR TCM[tiab] OR '
                '"chinese herbal medicine"[tiab] OR "herbal medicine"[tiab] OR '
                'acupuncture[tiab] OR electroacupuncture[tiab] OR moxibustion[tiab])'
            ),
        },
        {
            "label": "formula_specific",
            "query": (
                '("depression"[tiab] OR "depressive disorder"[tiab] OR '
                '"major depressive disorder"[tiab]) AND '
                '("Xiaoyao San"[tiab] OR "Jiawei Xiaoyao San"[tiab] OR '
                '"Chaihu Shugan San"[tiab] OR "Ganmai Dazao Tang"[tiab] OR '
                '"Banxia Houpu Tang"[tiab] OR "Danzhi Xiaoyao San"[tiab] OR '
                '"Guipi Tang"[tiab] OR "Yueju Wan"[tiab] OR "Suanzaoren Tang"[tiab] OR '
                '"Wendan Tang"[tiab] OR "Chaihu Jia Longgu Muli Tang"[tiab] OR '
                '"Yi Guan Jian"[tiab])'
            ),
        },
        {
            "label": "herb_specific",
            "query": (
                '("depression"[tiab] OR "depressive disorder"[tiab]) AND '
                '("Bupleurum"[tiab] OR Chaihu[tiab] OR "Glycyrrhiza"[tiab] OR '
                '"Angelica sinensis"[tiab] OR "Paeonia lactiflora"[tiab] OR '
                '"Poria cocos"[tiab] OR "Cyperus rotundus"[tiab] OR '
                '"Scutellaria baicalensis"[tiab] OR "Coptis chinensis"[tiab] OR '
                '"Aucklandia lappa"[tiab] OR "Salvia miltiorrhiza"[tiab] OR '
                '"Polygala tenuifolia"[tiab] OR "Ziziphus jujuba"[tiab])'
            ),
        },
        {
            "label": "target_mechanism",
            "query": (
                '("depression"[tiab] OR "depressive disorder"[tiab]) AND '
                '(BDNF[tiab] OR "5-HT"[tiab] OR serotonin[tiab] OR '
                '"TNF-alpha"[tiab] OR IL-6[tiab] OR CREB[tiab] OR SERT[tiab] OR '
                'MAPK[tiab] OR "PI3K-Akt"[tiab] OR "NF-kB"[tiab] OR Nrf2[tiab] OR '
                'mTOR[tiab] OR GSK-3β[tiab] OR "glucocorticoid receptor"[tiab])'
            ),
        },
        {
            "label": "pathway_mechanism",
            "query": (
                '("depression"[tiab] OR "depressive disorder"[tiab]) AND '
                '("neuroinflammation"[tiab] OR "HPA axis"[tiab] OR '
                '"tryptophan metabolism"[tiab] OR kynurenine[tiab] OR '
                '"gut-brain axis"[tiab] OR "oxidative stress"[tiab] OR '
                '"synaptic plasticity"[tiab] OR autophagy[tiab] OR apoptosis[tiab])'
            ),
        },
        {
            "label": "tcm_syndrome",
            "query": (
                '("depression"[tiab] OR "depressive disorder"[tiab]) AND '
                '("liver qi stagnation"[tiab] OR "heart-spleen deficiency"[tiab] OR '
                '"qi stagnation"[tiab] OR "blood deficiency"[tiab] OR '
                '"TCM syndrome"[tiab] OR syndrome[tiab] OR pattern[tiab] OR '
                '"syndrome differentiation"[tiab])'
            ),
        },
        {
            "label": "clinical_subtypes",
            "query": (
                '("postpartum depression"[tiab] OR "treatment-resistant depression"[tiab] OR '
                '"late-life depression"[tiab] OR "adolescent depression"[tiab]) AND '
                '("traditional chinese medicine"[tiab] OR acupuncture[tiab] OR '
                '"chinese herbal medicine"[tiab] OR formula[tiab] OR herb*[tiab])'
            ),
        },
        {
            "label": "network_pharmacology",
            "query": (
                '("depression"[tiab] OR "depressive disorder"[tiab]) AND '
                '("network pharmacology"[tiab] OR "systems pharmacology"[tiab] OR '
                '"molecular docking"[tiab]) AND '
                '("traditional chinese medicine"[tiab] OR formula[tiab] OR herb*[tiab])'
            ),
        },
    ]


# =========================
# PubMed API
# =========================
def esearch_count(session: requests.Session, query: str) -> int:
    """
    获取某个检索式的总命中数
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": 0,
        "sort": "relevance",
    }
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()["esearchresult"]
    return int(data["count"])


def esearch_page(
    session: requests.Session,
    query: str,
    retstart: int,
    retmax: int,
) -> List[str]:
    """
    按页获取 PMID 列表
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": retmax,
        "retstart": retstart,
        "sort": "relevance",
    }
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()["esearchresult"]
    return data.get("idlist", [])


def collect_pmids_for_query(
    session: requests.Session,
    query: str,
    max_per_query: int,
    page_size: int = 100,
) -> Tuple[int, List[str]]:
    """
    针对单条检索式，分批获取 PMID。
    返回：
      - PubMed 总命中数
      - 实际抓到的 PMID 列表（按检索顺序）
    """
    total_count = esearch_count(session, query)
    target_count = min(total_count, max_per_query)

    pmids: List[str] = []
    retstart = 0

    while len(pmids) < target_count:
        this_page = min(page_size, target_count - len(pmids))
        idlist = esearch_page(session, query, retstart=retstart, retmax=this_page)
        if not idlist:
            break
        pmids.extend(idlist)
        retstart += this_page
        time.sleep(0.34)  # 轻微限速，降低请求波动

    return total_count, pmids[:target_count]


# =========================
# PubMed 详情抓取
# =========================
def extract_doi(article) -> str:
    """
    从 ArticleIdList 中提取 DOI
    """
    doi = ""
    try:
        article_id_list = article["PubmedData"]["ArticleIdList"]
        for aid in article_id_list:
            try:
                if aid.attributes.get("IdType", "").lower() == "doi":
                    doi = str(aid)
                    break
            except Exception:
                continue
    except Exception:
        pass
    return doi


def extract_mesh_terms(medline_citation) -> List[str]:
    """
    提取 MeSH 词
    """
    mesh_terms = []
    try:
        mesh_list = medline_citation.get("MeshHeadingList", [])
        for mesh in mesh_list:
            try:
                descriptor = str(mesh["DescriptorName"])
                if descriptor:
                    mesh_terms.append(descriptor)
            except Exception:
                continue
    except Exception:
        pass
    return mesh_terms


def extract_publication_types(article_info) -> List[str]:
    """
    提取文献类型
    """
    types = []
    try:
        pub_types = article_info.get("PublicationTypeList", [])
        for pt in pub_types:
            pt_str = clean_text(str(pt))
            if pt_str:
                types.append(pt_str)
    except Exception:
        pass
    return types


def fetch_pubmed_details(pmid_list: List[str], source_labels_map: Dict[str, List[str]], batch_size: int = 50) -> List[Dict]:
    """
    批量获取文献详细信息
    """
    papers: List[Dict] = []

    for start in range(0, len(pmid_list), batch_size):
        batch = pmid_list[start:start + batch_size]
        if not batch:
            continue

        handle = Entrez.efetch(
            db="pubmed",
            id=",".join(batch),
            rettype="medline",
            retmode="xml",
        )

        records = Entrez.read(handle)
        articles = records.get("PubmedArticle", [])

        for article in articles:
            try:
                medline = article["MedlineCitation"]
                article_info = medline["Article"]

                pmid = str(medline["PMID"])
                title = clean_text(article_info.get("ArticleTitle", ""))

                abstract = ""
                if "Abstract" in article_info:
                    abstract_parts = article_info["Abstract"].get("AbstractText", [])
                    # 保留分段内容，避免丢失信息
                    abstract = " ".join(clean_text(x) for x in abstract_parts if clean_text(x))

                journal = ""
                try:
                    journal = clean_text(article_info["Journal"]["Title"])
                except Exception:
                    pass

                year = ""
                try:
                    year = safe_year(article_info["Journal"]["JournalIssue"]["PubDate"])
                except Exception:
                    try:
                        year = safe_year(article_info["ArticleDate"][0])
                    except Exception:
                        pass

                authors = []
                try:
                    author_list = article_info.get("AuthorList", [])
                    for author in author_list:
                        lastname = clean_text(author.get("LastName", ""))
                        firstname = clean_text(author.get("ForeName", ""))
                        collective = clean_text(author.get("CollectiveName", ""))

                        if collective:
                            authors.append(collective)
                        else:
                            full_name = clean_text(f"{lastname} {firstname}")
                            if full_name:
                                authors.append(full_name)
                except Exception:
                    pass

                doi = extract_doi(article)
                mesh_terms = extract_mesh_terms(medline)
                publication_types = extract_publication_types(article_info)

                source_labels = sorted(list(source_labels_map.get(pmid, [])))

                papers.append(
                    {
                        "PMID": pmid,
                        "Title": title,
                        "Abstract": abstract,
                        "Journal": journal,
                        "Year": year,
                        "Authors": "; ".join(authors),
                        "DOI": doi,
                        "MeshTerms": "; ".join(mesh_terms),
                        "PublicationTypes": "; ".join(publication_types),
                        "SourceQueries": "; ".join(source_labels),
                        "RetrievedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
            except Exception as e:
                print(f"解析失败 PMID={article.get('MedlineCitation', {}).get('PMID', 'UNKNOWN')}：{e}")

        time.sleep(0.34)

    return papers


# =========================
# 保存结果
# =========================
def save_json(data, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_csv(records: List[Dict], path: Path):
    df = pd.DataFrame(records)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def save_pmids_with_sources(pmid_sources: Dict[str, List[str]], path_csv: Path, path_txt: Path):
    rows = []
    with open(path_txt, "w", encoding="utf-8") as f:
        for pmid in pmid_sources.keys():
            f.write(f"{pmid}\n")
            rows.append(
                {
                    "PMID": pmid,
                    "SourceQueries": "; ".join(sorted(pmid_sources[pmid])),
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(path_csv, index=False, encoding="utf-8-sig")


def save_query_stats(query_stats: List[Dict], path_csv: Path, path_json: Path):
    df = pd.DataFrame(query_stats)
    df.to_csv(path_csv, index=False, encoding="utf-8-sig")
    save_json(query_stats, path_json)


# =========================
# 主流程
# =========================
def main():
    parser = argparse.ArgumentParser(description="Collect PubMed records for TCM depression KG")
    parser.add_argument("--max-per-query", type=int, default=100, help="每条检索式最多抓取多少篇")
    parser.add_argument("--page-size", type=int, default=100, help="每次 esearch 抓取多少 PMID")
    parser.add_argument("--batch-size", type=int, default=50, help="efetch 每批获取多少篇详情")
    parser.add_argument("--only-first-query", action="store_true", help="只跑第一条检索式，用于测试")
    parser.add_argument("--output-prefix", type=str, default=OUTPUT_PREFIX, help="输出文件前缀")
    args = parser.parse_args()

    query_specs = build_query_specs()
    if args.only_first_query:
        query_specs = query_specs[:1]

    session = build_session()

    pmid_sources_map: Dict[str, set] = defaultdict(set)
    query_stats: List[Dict] = []
    query_pmids_map: Dict[str, List[str]] = {}

    print("开始检索PubMed...")
    for spec in query_specs:
        label = spec["label"]
        query = spec["query"]

        print(f"\n[检索式] {label}")
        print(query)

        try:
            total_count, pmids = collect_pmids_for_query(
                session=session,
                query=query,
                max_per_query=args.max_per_query,
                page_size=args.page_size,
            )
        except Exception as e:
            print(f"检索失败：{label} -> {e}")
            query_stats.append(
                {
                    "Label": label,
                    "Query": query,
                    "PubMedCount": 0,
                    "Collected": 0,
                    "UniqueCollected": 0,
                    "Status": f"FAILED: {e}",
                }
            )
            continue

        # 本条检索式的 PMID 结果
        query_pmids_map[label] = pmids

        for pmid in pmids:
            pmid_sources_map[pmid].add(label)

        print(f"PubMed命中数：{total_count}")
        print(f"实际抓取数：{len(pmids)}")
        print(f"前10个PMID：{pmids[:10]}")

        query_stats.append(
            {
                "Label": label,
                "Query": query,
                "PubMedCount": total_count,
                "Collected": len(pmids),
                "UniqueCollected": len(set(pmids)),
                "Status": "OK",
            }
        )

        time.sleep(0.5)

    # 去重后的 PMID 列表
    unique_pmids = list(pmid_sources_map.keys())
    print("\n========================")
    print(f"去重后PMID总数：{len(unique_pmids)}")

    # 保存 PMID 与检索式映射
    pmid_sources_map_list = {k: sorted(list(v)) for k, v in pmid_sources_map.items()}
    save_pmids_with_sources(
        pmid_sources=pmid_sources_map_list,
        path_csv=RAW_DIR / f"{args.output_prefix}_pmids.csv",
        path_txt=RAW_DIR / f"{args.output_prefix}_pmids.txt",
    )
    save_json(query_pmids_map, RAW_DIR / f"{args.output_prefix}_query_pmids.json")
    save_query_stats(
        query_stats,
        RAW_DIR / f"{args.output_prefix}_query_stats.csv",
        RAW_DIR / f"{args.output_prefix}_query_stats.json",
    )

    if not unique_pmids:
        print("没有抓到任何PMID，程序结束。")
        return

    print("\n开始获取文献详细信息...")
    papers = fetch_pubmed_details(
        pmid_list=unique_pmids,
        source_labels_map=pmid_sources_map_list,
        batch_size=args.batch_size,
    )
    print(f"成功获取 {len(papers)} 篇文献详情")

    # 保存最终结果
    json_path = RAW_DIR / f"{args.output_prefix}.json"
    csv_path = RAW_DIR / f"{args.output_prefix}.csv"

    save_json(papers, json_path)
    save_csv(papers, csv_path)

    print("\n保存完成：")
    print(json_path)
    print(csv_path)
    print(RAW_DIR / f"{args.output_prefix}_pmids.csv")
    print(RAW_DIR / f"{args.output_prefix}_query_stats.csv")
    print("\n完成")


if __name__ == "__main__":
    main()