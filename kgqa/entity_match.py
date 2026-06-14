def extract_entity(question: str, entities: list[str]) -> str | None:
    q = question.lower()
    for e in entities:
        if e.lower() in q:
            return e
    return None