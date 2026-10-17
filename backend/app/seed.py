"""Idempotent authored content + explicitly synthetic demo records. No automatic seeding on startup."""
from datetime import timedelta
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app import models as m
from app.config import get_settings
from app.content.catalog import catalog, uid
from app.db import engine_for
from app.security.hashing import hash_password


def put(db, model, id, **fields):
    existing = db.get(model, id)
    if existing:
        return existing
    item = model(id=id, **fields)
    db.add(item); db.flush()
    return item


def seed_curriculum(db: Session):
    """Install authored teaching material only; create no users or learning history."""
    content = catalog()
    for e in content:
        put(db,m.Concept,e['concept_id'],slug=e['slug'],name=e['name'],description=e['explanation'])
        put(db,m.Exercise,e['id'],concept_id=e['concept_id'],title=e['title'],prompt=e['prompt'],code=e['code'],expected_output=e['expected_output'],
            flawed_explanation=e['flaw'],config=dict(categories=e['categories'],correct_category=e['broad'],correct_reason=e['reason']))
        for i,s in enumerate(e['segments']):
            put(db,m.ExplanationSegment,s['id'],exercise_id=e['id'],segment_order=i,text=s['text'],is_flawed=s['is_flawed'],
                issue_broad_category=e['broad'],issue_specific_reason=e['reason'])
        for h in e['hypotheses']:
            put(db,m.Hypothesis,h['id'],exercise_id=e['id'],key=h['key'],label=h['label'],description=h['description'],prior_weight=h['prior'])
            for r in h['rules']:
                put(db,m.EvidenceRule,uid(h['id']+'/'+r['key']),hypothesis_id=h['id'],evidence_key=r['key'],
                    polarity='support' if r['weight']>0 else 'contradict',weight=abs(r['weight']))
        current_followups = [f['id'] for f in e['followups']]
        db.execute(update(m.FollowUp).where(m.FollowUp.exercise_id == e['id'], m.FollowUp.id.not_in(current_followups)).values(active=False))
        for f in e['followups']:
            put(db,m.FollowUp,f['id'],exercise_id=e['id'],prompt=f['prompt'],code=f['code'],choices=f['choices'],correct_choice=f['correct_choice'],
                burden_score=f['burden'],estimated_effort=f['effort'],priority=f['priority'],explanation=f['explanation'])
            for hid,prediction in f['predictions'].items():
                put(db,m.FollowUpPrediction,uid(f['id']+'/'+hid),follow_up_id=f['id'],hypothesis_id=hid,predicted_answer_class=prediction)
        for s in e['support']:
            fields = {key:s[key] for key in ('hypothesis_id','title','explanation','worked_example','prediction_prompt','correct_choice','feedback_correct','feedback_incorrect','priority')}
            put(db,m.SupportModule,s['id'],exercise_id=e['id'],choices_json=s['choices'],**fields)
        for model,tasks in [(m.TransferTask,e['transfer']),(m.IndependentTask,[*e['independent'], *e['reflection']])]:
            for task in tasks:
                put(db,model,task['id'],concept_id=e['concept_id'],**{k:v for k,v in task.items() if k!='id'})
    db.flush()


def bootstrap_teacher(db: Session, username: str, password: str, *, synthetic: bool = False):
    """Create one explicitly provisioned teacher; never create learner records."""
    from app.services.teacher_invites import create_code
    from app.services.classroom import ensure_programming
    if len(password) < 10 or len(password.encode()) > 72:
        raise ValueError('Teacher password must be 10+ characters and at most 72 UTF-8 bytes.')
    if db.scalar(select(m.User).where(m.User.username == username)):
        raise ValueError('Teacher username already exists; credentials were not changed.')
    teacher=m.User(username=username,password_hash=hash_password(password),role='teacher',
                   is_synthetic=synthetic,data_origin='demo' if synthetic else 'pilot')
    db.add(teacher);db.flush()
    invitation=create_code(db,teacher.id)
    ensure_programming(db,teacher.id)
    return teacher, invitation


def seed(db: Session, password: str):
    """Explicit synthetic demonstration seed, retained for demos and isolated tests."""
    if len(password) < 10 or len(password.encode()) > 72:
        raise ValueError('Set DEMO_PASSWORD to 10+ characters and at most 72 UTF-8 bytes before seeding.')
    seed_curriculum(db)
    content = catalog()
    teacher = put(db,m.User,uid('teacher_demo'),username='teacher_demo',password_hash=hash_password(password),role='teacher',is_synthetic=True,data_origin='demo')
    from app.services.teacher_invites import create_code
    if not db.scalar(select(m.TeacherInviteCode).where(m.TeacherInviteCode.teacher_id == teacher.id)):
        create_code(db,teacher.id)
    from app.services.classroom import ensure_programming
    for owner in db.scalars(select(m.User).where(m.User.role=='teacher')):
        ensure_programming(db,owner.id)
    from app.services.journey_service import recalculate
    for index,name in enumerate(['learner_a','learner_b','learner_c']):
        learner = put(db,m.User,uid(name),username=name,password_hash=hash_password(password),role='learner',is_synthetic=True,data_origin='demo')
        put(db,m.LearnerProfile,uid(name+'/profile'),user_id=learner.id,display_name=name.replace('_',' ').title())
        put(db,m.TeacherAssignment,uid(name+'/teacher'),teacher_id=teacher.id,learner_id=learner.id)
        # Historical examples are separate from each user's live attempts.
        for outcome in ['PASS','FAIL']:
            e = content[0]
            baseline_id = uid(name+'/'+outcome+'/baseline')
            baseline = db.get(m.Attempt,baseline_id)
            if not baseline:
                baseline = put(db,m.Attempt,baseline_id,learner_id=learner.id,exercise_id=e['id'],stage='retention',status='complete',
                               is_synthetic=True,state={},created_at=m.now()-timedelta(days=60),started_at=m.now()-timedelta(days=60))
                patterns = [('caught_flaw','wrong_reason'),('missed_flaw','wrong_reason'),('caught_flaw','correct_reason')]
                for key in patterns[index]:
                    put(db,m.LearnerEvidence,uid(baseline_id+'/'+key),attempt_id=baseline.id,evidence_key=key,
                        value_json={'synthetic':True,'example':['correct-but-lucky','misconception','partial understanding'][index]},source='synthetic-baseline')
                recalculate(db,baseline)
                leading = baseline.state['assessment']['hypotheses'][0]['id']
                support = next(s for s in e['support'] if s['hypothesis_id']==leading and s['priority']==0)
                baseline.state = {**baseline.state,'support_id':support['id'],'independent_id':e['independent'][0]['id']}
                if index==2:
                    alternative = e['hypotheses'][1]['id']
                    put(db,m.LearnerChallenge,uid(baseline_id+'/challenge'),attempt_id=baseline.id,system_hypothesis_id=leading,
                        alternative_hypothesis_id=alternative,learner_reason='Synthetic example: I understood the assignment but misread the task.')
            put(db,m.RetentionCheck,uid(name+'/'+outcome+'/retention'),learner_id=learner.id,concept_id=e['concept_id'],baseline_attempt_id=baseline.id,
                check_date=m.now()-timedelta(days=30),is_synthetic=True,outcome=outcome,prompt=e['independent'][0]['prompt'],code=e['independent'][0]['code'],
                expected_output=e['independent'][0]['expected_output'],explanation=f'Synthetic {outcome} example for demonstrating the delayed-check workflow; not a real observation.',
                adaptation_required=outcome=='FAIL')
    db.commit()


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--demo',action='store_true',help='Explicitly include synthetic users and historical examples.')
    mode.add_argument('--curriculum-only',action='store_true',help='Install authored material without learner activity (default).')
    args=parser.parse_args()
    settings = get_settings()
    with Session(engine_for(settings.database_url,settings.database_schema),expire_on_commit=False) as db:
        if args.demo: seed(db,settings.demo_password)
        else: seed_curriculum(db);db.commit()
    print('Authored curriculum is ready.' if not args.demo else
          'Authored content and labelled synthetic demo records are ready. Demo users: learner_a, learner_b, learner_c, teacher_demo.')


if __name__ == '__main__':
    main()
