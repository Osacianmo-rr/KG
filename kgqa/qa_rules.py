def classify_question(q: str) -> str:
    q = q.lower()

    if "ingredient" in q or "contain" in q:
        return "herb_ingredient"

    if "target" in q or "act on" in q:
        return "herb_target"

    if "efficacy" in q or "effect" in q or "功效" in q:
        return "herb_efficacy"

    if "pair" in q or "combine" in q or "配伍" in q:
        return "pair_with"

    if "evidence" in q or "mention" in q or "paper" in q or "文献" in q:
        return "evidence_mentions"

    return "unknown"