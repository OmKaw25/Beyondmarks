from app import models as m
from app.services.journey_rules import adaptation_choice


def adapt(db, attempt, reason, source_check_id=None, verification_stage='independent'):
    from app.services.journey_service import recalculate, rows, record, support_candidates, update_state, new_task
    from app.services.practice_variants import fresh_support
    old = attempt.state.get('assessment', {'hypotheses':[], 'uncertain':True})
    new = recalculate(db, attempt)
    leading = new['hypotheses'][0]['id'] if new['hypotheses'] else None
    support = fresh_support(db, attempt, leading)
    task = new_task(db, attempt, independent=verification_stage != 'transfer', phase=verification_stage, fresh=True)
    choice = {'support':record(support), 'task':record(task)} if support and task else None
    if choice is None and verification_stage != 'transfer':
        exercise = db.get(m.Exercise, attempt.exercise_id)
        used = [r.support_module_id for r in rows(db, m.SupportAttempt, m.SupportAttempt.attempt_id == attempt.id)]
        if attempt.state.get('support_id'):
            used.append(attempt.state['support_id'])
        seen = [r.task_id for r in rows(db, m.IndependentAttempt, m.IndependentAttempt.learner_id == attempt.learner_id)]
        if attempt.state.get(verification_stage + '_id'):
            seen.append(attempt.state[verification_stage + '_id'])
        tasks = [record(r) for r in rows(db, m.IndependentTask, m.IndependentTask.concept_id == exercise.concept_id,
                                       m.IndependentTask.phase == verification_stage) if r.interaction_json.get('version') == 2]
        choice = adaptation_choice(leading, support_candidates(db, attempt), tasks, used, seen)
    event = m.AdaptationEvent(learner_id=attempt.learner_id, attempt_id=attempt.id, source_check_id=source_check_id,
                             old_assessment_json=old, new_assessment_json=new, reason=reason,
                             support_module_id=choice['support']['id'] if choice else None,
                             verification_task_id=choice['task']['id'] if choice and verification_stage != 'transfer' else None)
    db.add(event)
    update_state(attempt, adaptation=dict(old=old, new=new, reason=reason, is_synthetic=attempt.is_synthetic))
    if choice:
        update_state(attempt, adapting=True, support_id=choice['support']['id'], completed_support_id=None, verification_stage=verification_stage,
                     **{verification_stage + '_id': choice['task']['id']})
        attempt.stage = 'support'
    else:
        attempt.stage = 'review'
        update_state(attempt, review_reason='More evidence is needed, but no unused support and verification pair remains. Ask your teacher to review this investigation.')
