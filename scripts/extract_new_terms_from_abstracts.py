import re
import pandas as pd
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DICT_DIR = PROJECT_ROOT / "data" / "dictionaries"
CORPUS_FILE = PROCESSED_DIR / "high_quality_corpus.csv"
OUTPUT_TERMS = PROCESSED_DIR / "candidate_terms_from_abstracts.csv"

# 1. 加载文献摘要
df = pd.read_csv(CORPUS_FILE, encoding='utf-8-sig')
texts = (df['Title'].fillna('') + " " + df['Abstract'].fillna('')).tolist()
full_corpus = " ".join(texts)
print(f"总字符数: {len(full_corpus):,}")

# 2. 加载现有词典（种子词）
existing_terms = set()
for dict_file in DICT_DIR.glob("*.txt"):
    if dict_file.name == "herb_alias.csv":
        continue
    with open(dict_file, 'r', encoding='utf-8') as f:
        for line in f:
            term = line.strip()
            if term:
                existing_terms.add(term.lower())

print(f"现有种子词数量: {len(existing_terms)}")

# 3. 基于种子词扩展：匹配种子词后跟一个或多个单词（可能构成复合术语）
pattern_parts = []
for term in list(existing_terms)[:200]:  # 限制种子词数量，避免正则过长
    pattern_parts.append(re.escape(term))
if pattern_parts:
    regex = re.compile(r'\b(' + '|'.join(pattern_parts) + r')\s+([a-zA-Z\-]+(?:\s+[a-zA-Z\-]+){0,2})', re.IGNORECASE)
    matches = regex.findall(full_corpus)
    candidates = []
    for seed, suffix in matches:
        full_phrase = f"{seed} {suffix}".strip()
        candidates.append(full_phrase)
    candidate_counts = Counter(candidates)
    candidate_df = pd.DataFrame(candidate_counts.items(), columns=['Candidate_Term', 'Frequency'])
    candidate_df = candidate_df.sort_values('Frequency', ascending=False)
else:
    candidate_df = pd.DataFrame(columns=['Candidate_Term', 'Frequency'])

# 4. 另外，直接统计高频名词短语（不依赖种子词），作为补充
# 使用简单规则：连续2-4个单词，首字母大写或全大写（可能为术语）
words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b', full_corpus)
phrase_counts = Counter(words)
common_phrases = pd.DataFrame(phrase_counts.most_common(500), columns=['Candidate_Term', 'Frequency'])

# 5. 合并结果并保存
all_candidates = pd.concat([candidate_df, common_phrases], ignore_index=True)
all_candidates = all_candidates.drop_duplicates(subset=['Candidate_Term'])
all_candidates = all_candidates.sort_values('Frequency', ascending=False)

# 过滤掉已有词典中的词
existing_lower = {t.lower() for t in existing_terms}
all_candidates = all_candidates[~all_candidates['Candidate_Term'].str.lower().isin(existing_lower)]

all_candidates.to_csv(OUTPUT_TERMS, index=False, encoding='utf-8-sig')
print(f"候选新词已保存至: {OUTPUT_TERMS}")
print(f"候选词条总数: {len(all_candidates)}")
print("\n频率最高的前30个候选词:")
print(all_candidates.head(30))