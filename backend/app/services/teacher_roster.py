"""Enrollment-based roster; activity counts never determine student identity."""
from sqlalchemy import func, select
from app import models as m
from app.services.classroom import page_info


def roster_page(db, teacher_id, *, search='', limit=12, offset=0, include_samples=False):
    # EXISTS keeps one row per user regardless of any related activity.
    enrolled = select(m.TeacherAssignment.id).where(
        m.TeacherAssignment.teacher_id == teacher_id,
        m.TeacherAssignment.learner_id == m.User.id).exists()
    conditions = [enrolled, m.User.role == 'learner', m.User.active == True]
    if search.strip():
        conditions.append(m.User.username.icontains(search.strip(), autoescape=True))
    if not include_samples:
        conditions.extend([m.User.is_synthetic == False, m.User.data_origin != 'demo'])
    total = db.scalar(select(func.count()).select_from(m.User).where(*conditions))
    # Fetch only public roster fields, and only the requested page.
    users = list(db.execute(select(m.User.id, m.User.username, m.User.is_synthetic, m.User.data_origin)
        .where(*conditions).order_by(m.User.username, m.User.id).limit(limit).offset(offset)).mappings())
    ids = [user['id'] for user in users]
    counts = dict(db.execute(select(m.Attempt.learner_id, func.count())
        .where(m.Attempt.learner_id.in_(ids)).group_by(m.Attempt.learner_id)).all()) if ids else {}
    return {'learners': [dict(user, investigations=counts.get(user['id'], 0)) for user in users],
            'page': page_info(total, limit, offset)}
