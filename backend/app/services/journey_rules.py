from app.errors import fail
from app.services.support_engine import choose_support


def require_stage(current: str, allowed: list[str]):
    if current not in allowed:
        fail(409, 'STAGE_CONFLICT', 'This step has already been submitted or is not available yet. Reload to resume your current step.')


def public_task(task: dict) -> dict:
    view = {key: task[key] for key in ('id', 'prompt', 'code', 'explanation_prompt', 'reasoning_options')}
    interaction = task.get('interaction_json') or {}
    view['phase'] = task.get('phase')
    view['interaction'] = {key: interaction[key] for key in
                           ('format', 'difficulty', 'instruction', 'answer_label', 'answer_fields', 'choices') if key in interaction}
    return view


def adaptation_choice(hypothesis_id, modules, tasks, used_support, seen_tasks):
    support = choose_support(hypothesis_id, modules, used_support)
    fresh = sorted([t for t in tasks if t['id'] not in seen_tasks], key=lambda t: (t['priority'], t['id']))
    if not support or not fresh:
        return None
    return {'support': support, 'task': fresh[0]}
