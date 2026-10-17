"""Pure, deterministic evidence scores. These are not calibrated probabilities."""


def assess(hypotheses: list[dict], evidence: list[str]) -> dict:
    if not hypotheses:
        return {'hypotheses': [], 'uncertain': True}
    keys = set(evidence)
    rows = []
    for h in hypotheses:
        matched = [r for r in h['rules'] if r['key'] in keys]
        raw = h.get('prior', 1) + sum(r['weight'] for r in matched) - h.get('unresolved_penalty', 0)
        rows.append(dict(id=h['id'], label=h['label'], description=h.get('description', ''), raw=max(0, raw),
                         supporting_evidence=[r['key'] for r in matched if r['weight'] > 0],
                         contradicting_evidence=[r['key'] for r in matched if r['weight'] < 0]))
    total = sum(r['raw'] for r in rows)
    for row in rows:
        score = row.pop('raw') / total if total > 0 else 1 / len(rows)
        row.update(score=score, confidence='High' if score >= .75 else 'Medium' if score >= .5 else 'Low')
    rows.sort(key=lambda r: (-r['score'], r['id']))
    uncertain = not keys or (len(rows) > 1 and rows[0]['score'] - rows[1]['score'] < .15)
    return {'hypotheses': rows, 'uncertain': uncertain}
