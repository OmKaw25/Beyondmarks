"""Real seven/thirty-day retrieval checks, released by server time only."""
from datetime import timedelta
from sqlalchemy import select
from app import models as m
from app.errors import fail
from app.services.assessment_service import evaluate_task
from app.services.journey_rules import public_task


def schedule_for_attempt(db, attempt):
    if attempt.status != 'complete' or attempt.completed_at is None or attempt.is_synthetic:
        return []
    learner = db.scalar(select(m.User).where(m.User.id == attempt.learner_id).with_for_update())
    if not learner or learner.is_synthetic or learner.data_origin == 'demo':
        return []
    from app.content.practice_variants import SUPPORTED, task_variant
    from app.services.practice_variants import save_shared
    exercise = db.get(m.Exercise, attempt.exercise_id)
    concept = db.get(m.Concept, exercise.concept_id)
    if concept.slug not in SUPPORTED:
        fail(409, 'RETENTION_CONTENT_UNAVAILABLE', 'This concept needs an authored delayed check before scheduling.')
    existing = list(db.scalars(select(m.DelayedCheck).where(m.DelayedCheck.baseline_attempt_id == attempt.id)))
    intervals = {row.interval_days for row in existing}
    used = set(db.scalars(select(m.IndependentAttempt.task_id).where(m.IndependentAttempt.learner_id == learner.id)))
    used.update(db.scalars(select(m.DelayedCheck.task_id).where(m.DelayedCheck.learner_id == learner.id)))
    for active in db.scalars(select(m.Attempt).where(m.Attempt.learner_id == learner.id)):
        used.update(active.state.get(key) for key in ('independent_id', 'reflection_id'))
    for days in (7, 30):
        if days in intervals:
            continue
        index = 0
        while True:
            fields = task_variant(concept.slug, 'independent', index)
            if fields['id'] not in used:
                break
            index += 1
        fields['concept_id'] = concept.id
        task = save_shared(db, m.IndependentTask, fields)
        # Snapshot content and grading keys so later curriculum edits cannot alter this check.
        task_snapshot = {key: getattr(task, key) for key in (
            'id', 'phase', 'prompt', 'code', 'expected_output', 'explanation_prompt',
            'reasoning_options', 'correct_tag', 'interaction_json')}
        check = m.DelayedCheck(learner_id=learner.id, concept_id=concept.id, baseline_attempt_id=attempt.id,
                               interval_days=days, due_at=attempt.completed_at + timedelta(days=days),
                               task_id=task.id, task_json=task_snapshot)
        db.add(check)
        existing.append(check)
        used.add(task.id)
    db.flush()
    return existing


def check_for(db, user, check_id, lock=False):
    query = select(m.DelayedCheck).where(m.DelayedCheck.id == check_id, m.DelayedCheck.learner_id == user.id)
    check = db.scalar(query.with_for_update().execution_options(populate_existing=True) if lock else query)
    if not check:
        fail(404, 'NOT_FOUND', 'This delayed check was not found.')
    return check


def check_view(db, check, detail=False, timestamp=None, learner=None, baseline=None):
    timestamp = timestamp or m.now()
    status = ('passed' if check.result_json['passed'] else 'failed') if check.completed_at else ('due' if timestamp >= check.due_at else 'scheduled')
    adaptation = db.get(m.Attempt, check.adaptation_attempt_id) if check.adaptation_attempt_id else None
    learner = learner or db.get(m.User, check.learner_id)
    baseline = baseline or db.get(m.Attempt, check.baseline_attempt_id)
    # Provenance follows the account/baseline even if an operator classifies old activity later.
    synthetic = learner.is_synthetic or baseline.is_synthetic or learner.data_origin == 'demo'
    next_url = (f'/{adaptation.stage}/{adaptation.id}' if adaptation.stage not in ('retention', 'review')
                else f'/retention/{adaptation.id}') if adaptation else None
    view = dict(id=check.id, baseline_attempt_id=check.baseline_attempt_id, concept_id=check.concept_id,
                concept=db.get(m.Concept, check.concept_id).name, interval_days=check.interval_days,
                due_at=check.due_at, status=status, completed_at=check.completed_at,
                adaptation_attempt_id=check.adaptation_attempt_id, next_url=next_url,
                is_synthetic=synthetic, data_origin='demo' if synthetic else learner.data_origin)
    if detail:
        view.update(task=public_task(check.task_json) if timestamp >= check.due_at else None,
                    result=check.result_json, response=check.answer_json)
    return view


def list_checks(db, user, include_demo=False, include_completed=False):
    checks = list(db.scalars(select(m.DelayedCheck).where(m.DelayedCheck.learner_id == user.id)
                            .order_by(m.DelayedCheck.due_at, m.DelayedCheck.id)))
    baselines = {a.id: a for a in db.scalars(select(m.Attempt).where(
        m.Attempt.id.in_({check.baseline_attempt_id for check in checks})))} if checks else {}
    timestamp = m.now()
    views = []
    for check in checks:
        view = check_view(db, check, timestamp=timestamp, learner=user, baseline=baselines[check.baseline_attempt_id])
        if view['is_synthetic'] and not include_demo:
            continue
        if include_completed:
            # Teacher review gets submitted evidence, never the reserved task or answer key.
            view.update(response=check.answer_json if check.completed_at else None,
                        result=check.result_json if check.completed_at else None)
        views.append(view)
    return {'checks': views}


def submit_check(db, user, check_id, payload):
    check = check_for(db, user, check_id, lock=True)
    timestamp = m.now()
    if check.completed_at:
        fail(409, 'CHECK_RECORDED', 'This answer is already saved and cannot be replaced.')
    if timestamp < check.due_at:
        fail(409, 'CHECK_NOT_DUE', 'This check becomes available on its scheduled date.')
    if payload.reasoning_tag not in {option['value'] for option in check.task_json['reasoning_options']}:
        fail(422, 'INVALID_REASON', 'Choose one of the available reasoning descriptions.')
    response = payload.model_dump()
    result = evaluate_task(check.task_json, response)
    check.answer_json, check.result_json, check.completed_at = response, result, timestamp
    if not result['passed']:
        from app.services.journey_service import append_evidence
        from app.services.adaptation_engine import adapt
        db.scalar(select(m.User).where(m.User.id == user.id).with_for_update())
        prior = list(db.scalars(select(m.DelayedCheck).where(
            m.DelayedCheck.baseline_attempt_id == check.baseline_attempt_id,
            m.DelayedCheck.adaptation_attempt_id.is_not(None))))
        adaptation = next((a for c in prior if (a := db.get(m.Attempt, c.adaptation_attempt_id)) and a.status == 'active'), None)
        if adaptation is None:
            baseline = db.get(m.Attempt, check.baseline_attempt_id)
            sample = user.is_synthetic or baseline.is_synthetic or user.data_origin == 'demo'
            adaptation = m.Attempt(learner_id=user.id, exercise_id=baseline.exercise_id, is_synthetic=sample,
                                   state={'delayed_check_id': check.id})
            db.add(adaptation)
            db.flush()
            append_evidence(db, adaptation, 'independent_failed', dict(check_id=check.id, result=result), 'delayed-check')
            adapt(db, adaptation, reason=f'The {check.interval_days}-day check needs more support. Try a fresh example and another independent check.')
        else:
            append_evidence(db, adaptation, 'independent_failed', dict(check_id=check.id, result=result), 'delayed-check')
        check.adaptation_attempt_id = adaptation.id
    db.flush()
    return check_view(db, check, detail=True)
