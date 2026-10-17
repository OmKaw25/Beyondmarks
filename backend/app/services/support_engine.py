def choose_support(hypothesis_id: str | None, modules: list[dict], excluded_ids: list[str]) -> dict | None:
    eligible = [m for m in modules if m['id'] not in excluded_ids and m['hypothesis_id'] == hypothesis_id]
    return min(eligible, key=lambda m: (m['priority'], m['id'])) if eligible else None
