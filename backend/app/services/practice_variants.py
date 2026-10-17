"""Persist shared variants on demand; keep each learner's retries reproducible."""
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app import models as m
from app.content.catalog import uid
from app.content.practice_variants import SUPPORTED, support_variant, task_variant


def save_shared(db, model, fields):
    db.execute(insert(model).values(**fields).on_conflict_do_nothing(index_elements=['id']))
    return db.get(model, fields['id'])


def fresh_support(db, attempt, hypothesis_id):
    exercise = db.get(m.Exercise, attempt.exercise_id)
    concept = db.get(m.Concept, exercise.concept_id)
    if concept.slug not in SUPPORTED:
        return None
    seen = set(db.scalars(select(m.SupportModule.worked_example)
        .join(m.SupportAttempt, m.SupportAttempt.support_module_id == m.SupportModule.id)
        .join(m.Attempt, m.Attempt.id == m.SupportAttempt.attempt_id)
        .where(m.Attempt.learner_id == attempt.learner_id, m.SupportModule.exercise_id == exercise.id)))
    current = db.get(m.SupportModule, attempt.state.get('support_id')) if attempt.state.get('support_id') else None
    if current:
        seen.add(current.worked_example)
    index = 0
    while True:
        fields = support_variant(concept.slug, index)
        if fields['worked_example'] not in seen:
            break
        index += 1
    fields.update(id=uid(f'{exercise.id}/practice-v3/support/{hypothesis_id}/{index}'),
                  exercise_id=exercise.id, hypothesis_id=hypothesis_id, priority=1000 + index)
    hypothesis = db.get(m.Hypothesis, hypothesis_id) if hypothesis_id else None
    if hypothesis and hypothesis.key == 'reading':
        fields['explanation'] = 'First identify exactly which result the question asks for. ' + fields['explanation']
    return save_shared(db, m.SupportModule, fields)


def fresh_task(db, attempt, phase):
    exercise = db.get(m.Exercise, attempt.exercise_id)
    concept = db.get(m.Concept, exercise.concept_id)
    if concept.slug not in SUPPORTED:
        return None
    model = m.TransferTask if phase == 'transfer' else m.IndependentTask
    responses = m.TransferAttempt if phase == 'transfer' else m.IndependentAttempt
    task_column = responses.transfer_task_id if phase == 'transfer' else responses.task_id
    seen = set(db.scalars(select(task_column).where(responses.learner_id == attempt.learner_id)))
    if model is m.IndependentTask:
        seen.update(db.scalars(select(m.DelayedCheck.task_id).where(m.DelayedCheck.learner_id == attempt.learner_id)))
    seen.add(attempt.state.get(phase + '_id'))
    index = 0
    while True:
        fields = task_variant(concept.slug, phase, index)
        if fields['id'] not in seen:
            break
        index += 1
    fields['concept_id'] = concept.id
    return save_shared(db, model, fields)
