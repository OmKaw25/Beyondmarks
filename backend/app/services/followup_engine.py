def select_followup(candidates: list[dict], active_hypotheses: list[str], answered_ids: list[str]) -> dict | None:
    if len(active_hypotheses) < 2:
        return None
    eligible = []
    for c in candidates:
        if not c.get('active', True) or c['id'] in answered_ids:
            continue
        if not all(h in c['predictions'] for h in active_hypotheses):
            continue
        predictions = {h: c['predictions'][h] for h in active_hypotheses}
        distinct = len(set(predictions.values()))
        if distinct < 2:
            continue
        divergence = distinct / len(active_hypotheses)
        eligible.append(dict(c, predictions=predictions, divergence=divergence,
                             selection_score=divergence * 100 - c['burden'],
                             rationale='The plausible explanations predict different responses. This question helps distinguish them with a short interaction.'))
    if not eligible:
        return None
    return min(eligible, key=lambda c: (-c['selection_score'], -c['divergence'], c['burden'], c['effort'], c['priority'], c['id']))
