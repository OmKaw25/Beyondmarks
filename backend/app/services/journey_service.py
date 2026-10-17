"""Transactional learner journey. All mutations lock the owned attempt row."""
import logging
from sqlalchemy import select
from app import models as m
from app.errors import fail
from app.services.diagnostic_engine import assess
from app.services.followup_engine import select_followup
from app.services.journey_rules import require_stage, public_task
from app.services.support_engine import choose_support
from app.services.assessment_service import evaluate_task

log = logging.getLogger('beyond-marks.journey')


def record(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def rows(db, model, *conditions):
    return list(db.scalars(select(model).where(*conditions)))


def owned(db, learner_id, attempt_id, lock=False):
    query = select(m.Attempt).where(m.Attempt.id == attempt_id, m.Attempt.learner_id == learner_id)
    attempt = db.scalar(query.with_for_update() if lock else query)
    if not attempt:
        fail(404, 'NOT_FOUND', 'This investigation was not found.')
    return attempt


def update_state(attempt, **values):
    attempt.state = {**attempt.state, **values}


def append_evidence(db, attempt, key, value, source):
    db.add(m.LearnerEvidence(attempt_id=attempt.id, evidence_key=key, value_json=value, source=source))


def save_self_report(db, attempt, payload, phase):
    report = {name: getattr(payload, name, None) for name in ('confidence', 'context', 'context_note')}
    if not any(report.values()):
        return None
    report.update(phase=phase, submitted_at=m.now().isoformat(), interpretation='Learner-reported context; not a verified cause.')
    append_evidence(db, attempt, 'learner_self_report', report, 'self-report')
    update_state(attempt, self_report=report)
    return report


def agency(db, attempt, payload):
    previous = attempt.state.get('agency', {})
    state = {'paused': False, 'help_requested': False, **previous, 'updated_at': m.now().isoformat()}
    if payload.action == 'pause':
        if attempt.status != 'active':
            fail(409, 'ALREADY_COMPLETE', 'This investigation is already complete.')
        state.update(paused=True, reason=payload.reason)
    elif payload.action == 'resume':
        state.update(paused=False)
    else:
        state.update(help_requested=True, help_reason=payload.reason)
    append_evidence(db, attempt, 'learner_' + payload.action, dict(action=payload.action, reason=payload.reason, stage=attempt.stage), 'learner-agency')
    update_state(attempt, agency=state)


def recalculate(db, attempt):
    db.flush()
    hypotheses = rows(db, m.Hypothesis, m.Hypothesis.exercise_id == attempt.exercise_id)
    definitions = []
    for h in hypotheses:
        rules = rows(db, m.EvidenceRule, m.EvidenceRule.hypothesis_id == h.id)
        definitions.append(dict(id=h.id, label=h.label, description=h.description, prior=h.prior_weight,
                                rules=[dict(key=r.evidence_key, weight=r.weight if r.polarity == 'support' else -r.weight) for r in rules]))
    evidence = rows(db, m.LearnerEvidence, m.LearnerEvidence.attempt_id == attempt.id)
    result = assess(definitions, [e.evidence_key for e in evidence])
    result['limits'] = 'These are working explanations, not a diagnosis. A single answer can fit more than one explanation; confidence and context are learner reports, not proof of a cause.'
    for h in result['hypotheses']:
        db.add(m.HypothesisAssessment(attempt_id=attempt.id, hypothesis_id=h['id'], score=h['score'],
                                     confidence_label=h['confidence'], evidence_summary=h))
    update_state(attempt, assessment=result)
    log.info('attempt=%s stage=%s hypotheses=%d uncertain=%s', attempt.id, attempt.stage, len(hypotheses), result['uncertain'])
    return result


def support_candidates(db, attempt):
    return [record(r) for r in rows(db, m.SupportModule, m.SupportModule.exercise_id == attempt.exercise_id)]


def set_support(db, attempt, general=False, fresh=False):
    assessment = attempt.state.get('assessment', {'hypotheses': []})
    hid = assessment['hypotheses'][0]['id'] if assessment['hypotheses'] and not general else None
    used = [r.support_module_id for r in rows(db, m.SupportAttempt, m.SupportAttempt.attempt_id == attempt.id)]
    seen_code = set(db.scalars(select(m.SupportModule.worked_example)
        .join(m.SupportAttempt, m.SupportAttempt.support_module_id == m.SupportModule.id)
        .join(m.Attempt, m.Attempt.id == m.SupportAttempt.attempt_id)
        .where(m.Attempt.learner_id == attempt.learner_id, m.SupportModule.exercise_id == attempt.exercise_id)))
    candidates = [s for s in support_candidates(db, attempt) if s['worked_example'] not in seen_code]
    module = None if fresh else choose_support(hid, candidates, used)
    if not module:
        from app.services.practice_variants import fresh_support
        generated = fresh_support(db, attempt, hid)
        module = record(generated) if generated else None
    if not module:
        attempt.stage = 'review'
        update_state(attempt, review_reason='The authored support options are exhausted. Ask your teacher to review the evidence.')
        return
    update_state(attempt, support_id=module['id'], completed_support_id=None, result=None)
    attempt.stage = 'support'


def new_task(db, attempt, independent=True, phase=None, fresh=False):
    phase = phase or ('independent' if independent else 'transfer')
    from app.services.practice_variants import fresh_task
    if fresh:
        return fresh_task(db, attempt, phase)
    exercise = db.get(m.Exercise, attempt.exercise_id)
    model = m.IndependentTask if independent else m.TransferTask
    attempts = rows(db, m.IndependentAttempt if independent else m.TransferAttempt,
                    (m.IndependentAttempt.learner_id if independent else m.TransferAttempt.learner_id) == attempt.learner_id)
    seen = {r.task_id if independent else r.transfer_task_id for r in attempts}
    if independent:
        seen.update(db.scalars(select(m.DelayedCheck.task_id).where(m.DelayedCheck.learner_id == attempt.learner_id)))
    tasks = rows(db, model, model.concept_id == exercise.concept_id, model.phase == phase)
    eligible = sorted([t for t in tasks if t.id not in seen and t.interaction_json.get('version') == 2], key=lambda t: (t.priority, t.id))
    return eligible[0] if eligible else fresh_task(db, attempt, phase)


def task_view(db, attempt):
    if attempt.stage == 'transfer':
        task = db.get(m.TransferTask, attempt.state.get('transfer_id'))
    elif attempt.stage in ('independent', 'reflection'):
        task = db.get(m.IndependentTask, attempt.state.get(attempt.stage + '_id'))
    else:
        return None
    return public_task(record(task)) if task else None


def snapshot(db, attempt):
    independent = attempt.stage in ('independent', 'reflection')
    exercise = db.get(m.Exercise, attempt.exercise_id)
    segments = sorted(rows(db, m.ExplanationSegment, m.ExplanationSegment.exercise_id == exercise.id), key=lambda s: s.segment_order)
    support = db.get(m.SupportModule, attempt.state['support_id']) if attempt.state.get('support_id') and attempt.stage == 'support' else None
    selected = attempt.state.get('selection')
    followup = db.get(m.FollowUp, selected['id']) if selected and attempt.stage == 'follow-up' else None
    return dict(id=attempt.id, title=exercise.title, stage=attempt.stage, status=attempt.status,
                is_synthetic=attempt.is_synthetic,
                agency=attempt.state.get('agency', {'paused': False, 'help_requested': False}),
                self_report=attempt.state.get('self_report') if not independent else None,
                exercise=dict(id=exercise.id, prompt=exercise.prompt, code=exercise.code, expected_output=exercise.expected_output,
                              segments=[dict(id=s.id, text=s.text) for s in segments], categories=exercise.config['categories']) if not independent else None,
                assessment=attempt.state.get('assessment') if not independent else None, challenge=attempt.state.get('challenge') if not independent else None,
                selection=selected if not independent else None, inconclusive=attempt.state.get('inconclusive', False) if not independent else False,
                followup=dict(id=followup.id, prompt=followup.prompt, code=followup.code, choices=followup.choices) if followup else None,
                support={k: getattr(support, k) for k in ('id','title','explanation','worked_example','prediction_prompt','choices_json')} if support else None,
                support_completed=attempt.stage == 'support' and attempt.state.get('completed_support_id') == attempt.state.get('support_id'),
                task=task_view(db, attempt), result=attempt.state.get('result') if not independent else None,
                adaptation=attempt.state.get('adaptation') if not independent else None, review_reason=attempt.state.get('review_reason'),
                next_url=f'/{attempt.stage}/{attempt.id}' if attempt.stage not in ('retention','review') else f'/retention/{attempt.id}')


def start(db, user, exercise_id):
    exercise = db.get(m.Exercise, exercise_id)
    if not exercise or not exercise.active:
        fail(404, 'NOT_FOUND', 'This exercise is not available.')
    # Serialize check-and-create across browser tabs before reading attempts.
    db.scalar(select(m.User).where(m.User.id == user.id).with_for_update())
    existing = db.scalar(select(m.Attempt).where(m.Attempt.learner_id == user.id, m.Attempt.exercise_id == exercise_id,
                                               m.Attempt.status == 'active', m.Attempt.is_synthetic == False).order_by(m.Attempt.created_at.desc()))
    if existing:
        return snapshot(db, existing)
    attempt = m.Attempt(learner_id=user.id, exercise_id=exercise_id, state={})
    db.add(attempt); db.flush()
    return snapshot(db, attempt)


def correct(db, attempt, payload):
    require_stage(attempt.stage, ['investigate'])
    exercise = db.get(m.Exercise, attempt.exercise_id)
    segments = rows(db, m.ExplanationSegment, m.ExplanationSegment.exercise_id == exercise.id)
    selected = set(str(i) for i in payload.segment_ids)
    valid_ids = {s.id for s in segments}
    if not selected <= valid_ids:
        fail(422, 'INVALID_SEGMENT', 'Select explanation segments from this exercise.')
    options = exercise.config['categories'].get(payload.broad_category, [])
    if payload.specific_reason not in [o['value'] for o in options]:
        fail(422, 'INVALID_REASON', 'Choose a reason offered for this category.')
    expected = {s.id for s in segments if s.is_flawed}
    value = payload.model_dump(mode='json')
    append_evidence(db, attempt, 'caught_flaw' if selected == expected else 'missed_flaw', value, 'correction')
    reason_correct = payload.specific_reason == exercise.config['correct_reason'] and payload.broad_category == exercise.config['correct_category']
    append_evidence(db, attempt, 'correct_reason' if reason_correct else 'wrong_reason', value, 'correction')
    save_self_report(db, attempt, payload, 'investigate')
    attempt.stage = 'diagnosis'
    recalculate(db, attempt)


def challenge(db, attempt, payload):
    require_stage(attempt.stage, ['diagnosis'])
    alternative = db.get(m.Hypothesis, str(payload.alternative_hypothesis_id))
    if not alternative or alternative.exercise_id != attempt.exercise_id:
        fail(422, 'INVALID_HYPOTHESIS', 'Choose an explanation from this investigation.')
    if attempt.state.get('challenge'):
        fail(409, 'CHALLENGE_RECORDED', 'Your disagreement is already recorded. Continue to the follow-up.')
    leading = attempt.state['assessment']['hypotheses'][0]['id']
    db.add(m.LearnerChallenge(attempt_id=attempt.id, system_hypothesis_id=leading,
                             alternative_hypothesis_id=alternative.id, learner_reason=payload.reason))
    append_evidence(db, attempt, f'challenge:{alternative.id}', payload.model_dump(mode='json'), 'challenge')
    update_state(attempt, challenge=dict(alternative=alternative.label, reason=payload.reason))
    recalculate(db, attempt)


def select_next(db, attempt):
    require_stage(attempt.stage, ['diagnosis'])
    candidates = []
    for f in rows(db, m.FollowUp, m.FollowUp.exercise_id == attempt.exercise_id):
        predictions = rows(db, m.FollowUpPrediction, m.FollowUpPrediction.follow_up_id == f.id)
        candidates.append(dict(id=f.id, active=f.active, burden=f.burden_score, effort=f.estimated_effort, priority=f.priority,
                               explanation=f.explanation,
                               predictions={p.hypothesis_id:p.predicted_answer_class for p in predictions}))
    active = [h['id'] for h in attempt.state['assessment']['hypotheses'] if h['score'] > 0]
    selected = select_followup(candidates, active, [])
    context = attempt.state.get('self_report', {}).get('context')
    preferred_priority = 1 if context == 'misread' else 2 if context in ('time_pressure', 'incomplete_work') else None
    if preferred_priority is not None:
        contextual = select_followup([c for c in candidates if c['priority'] == preferred_priority], active, [])
        if contextual:
            selected = contextual
    if not selected:
        rationale = 'No available question meaningfully separates the current explanations. A general concept lesson is available; the cause remains inconclusive.'
        db.add(m.FollowUpSelection(attempt_id=attempt.id, follow_up_id=None, divergence_score=0, burden_penalty=0, final_score=0, rationale=rationale))
        update_state(attempt, inconclusive=True, selection=None)
        set_support(db, attempt, general=True)
        return
    labels = {h['id']:h['label'] for h in attempt.state['assessment']['hypotheses']}
    selected['rationale'] += ' ' + selected.get('explanation', '')
    if preferred_priority is not None:
        selected['rationale'] += ' Your reported context helped choose this question; it did not change the evidence scores.'
    selected['prediction_labels'] = [dict(hypothesis=labels[h], answer=a) for h,a in selected['predictions'].items()]
    update_state(attempt, selection=selected)
    db.add(m.FollowUpSelection(attempt_id=attempt.id, follow_up_id=selected['id'], divergence_score=selected['divergence'],
                              burden_penalty=selected['burden'], final_score=selected['selection_score'], rationale=selected['rationale']))
    attempt.stage = 'follow-up'


def answer_followup(db, attempt, payload):
    require_stage(attempt.stage, ['follow-up'])
    selected = attempt.state['selection']
    followup = db.get(m.FollowUp, selected['id'])
    if payload.answer not in [c['value'] for c in followup.choices]:
        fail(422, 'INVALID_CHOICE', 'Choose one of the offered answers.')
    matched = [h for h, answer in selected['predictions'].items() if answer == payload.answer]
    for hid in matched:
        append_evidence(db, attempt, f'predicts:{hid}', {'answer':payload.answer, 'follow_up_id':followup.id}, 'follow-up')
    if not matched:
        append_evidence(db, attempt, 'unexplained_followup', {'answer':payload.answer}, 'follow-up')
    recalculate(db, attempt)
    set_support(db, attempt)


def answer_support(db, attempt, payload):
    require_stage(attempt.stage, ['support'])
    if str(payload.support_id) != attempt.state['support_id']:
        fail(409, 'STALE_SUPPORT', 'The support has changed. Refresh to see your current step.')
    if attempt.state.get('completed_support_id') == attempt.state['support_id']:
        fail(409, 'SUPPORT_RECORDED', 'Your prediction is already recorded. Continue to the next step.')
    module = db.get(m.SupportModule, attempt.state['support_id'])
    if payload.answer not in [c['value'] for c in module.choices_json]:
        fail(422, 'INVALID_CHOICE', 'Choose one of the offered predictions.')
    correct_answer = payload.answer == module.correct_choice
    db.add(m.SupportAttempt(attempt_id=attempt.id, support_module_id=module.id, selected_choice=payload.answer, correct=correct_answer))
    append_evidence(db, attempt, 'support_correct' if correct_answer else 'support_incorrect', {'module_id':module.id, 'answer':payload.answer}, 'support')
    update_state(attempt, completed_support_id=module.id,
                 result={'correct':correct_answer, 'feedback':module.feedback_correct if correct_answer else module.feedback_incorrect})


def continue_support(db, attempt, payload):
    require_stage(attempt.stage, ['support'])
    if str(payload.support_id) != attempt.state['support_id']:
        fail(409, 'STALE_SUPPORT', 'The support has changed. Refresh to see your current step.')
    if attempt.state.get('completed_support_id') != attempt.state['support_id']:
        fail(409, 'SUPPORT_REQUIRED', 'Submit your prediction before continuing.')
    # Check the saved response, not a transient feedback banner. Wrong practice
    # answers cannot unlock verification by pressing Continue.
    response = db.scalar(select(m.SupportAttempt).where(m.SupportAttempt.attempt_id == attempt.id,
                         m.SupportAttempt.support_module_id == attempt.state['support_id'])
                         .order_by(m.SupportAttempt.completed_at.desc(), m.SupportAttempt.id.desc()))
    if not response or not response.correct:
        set_support(db, attempt, fresh=True)
        return
    update_state(attempt, result=None)
    if attempt.state.get('adapting'):
        attempt.stage = attempt.state.get('verification_stage', 'independent')
    else:
        task = new_task(db, attempt, independent=False)
        if not task:
            attempt.stage = 'review'
            update_state(attempt, review_reason='You have completed the available transfer task for this concept. Ask your teacher for another context.')
        else:
            update_state(attempt, transfer_id=task.id)
            attempt.stage = 'transfer'


def answer_task(db, attempt, payload, independent, reflection=False):
    phase = 'reflection' if reflection else 'independent' if independent else 'transfer'
    require_stage(attempt.stage, [phase])
    task_id = attempt.state[phase + '_id']
    if str(payload.task_id) != task_id:
        fail(409, 'STALE_TASK', 'This task has changed. Refresh before submitting your current response.')
    task = db.get(m.IndependentTask if independent else m.TransferTask, task_id)
    if payload.reasoning_tag not in [o['value'] for o in task.reasoning_options]:
        fail(422, 'INVALID_REASON', 'Choose one of the available reasoning descriptions.')
    result = evaluate_task(record(task), payload.model_dump())
    result['phase'] = phase
    report = save_self_report(db, attempt, payload, phase)
    if report:
        result['self_report'] = report
    fields = dict(learner_id=attempt.learner_id, attempt_id=attempt.id, answer=payload.answer, explanation=payload.explanation,
                  correct=result['correct'], evidence_json=result)
    db.add(m.IndependentAttempt(task_id=task.id, **fields) if independent else m.TransferAttempt(transfer_task_id=task.id, **fields))
    key = phase + ('_passed' if result['passed'] else '_failed')
    append_evidence(db, attempt, key, result, phase)
    update_state(attempt, result=result)
    if not result['passed']:
        from app.services.adaptation_engine import adapt
        adapt(db, attempt, reason={'transfer':'Transfer practice', 'independent':'Independent verification',
                                  'reflection':'The reflection challenge'}[phase] +
              ' did not yet show the result and supporting reasoning. Try a fresh example, then a different check.',
              verification_stage=phase)
        return
    if independent:
        recalculate(db, attempt)
        if reflection:
            attempt.stage, attempt.status, attempt.completed_at = 'retention', 'complete', m.now()
            from app.services.delayed_retention import schedule_for_attempt
            schedule_for_attempt(db, attempt)
        else:
            task = new_task(db, attempt, phase='reflection')
            if task:
                update_state(attempt, reflection_id=task.id)
                attempt.stage = 'reflection'
            else:
                attempt.stage = 'review'
                update_state(attempt, review_reason='No unseen reflection challenge remains. Ask your teacher for a new challenge.')
    else:
        task = new_task(db, attempt)
        if task:
            update_state(attempt, independent_id=task.id)
            attempt.stage = 'independent'
        else:
            attempt.stage = 'review'
            update_state(attempt, review_reason='No unseen independent task remains. Ask your teacher for a new verification task.')
