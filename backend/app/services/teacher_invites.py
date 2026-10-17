"""Reusable teacher-owned invitation codes; never grant learner assignments."""
import secrets
from sqlalchemy import select
from app.models import TeacherInviteCode, User
from app.errors import fail


def create_code(db, teacher_id, invited_by_id=None):
    code = TeacherInviteCode(teacher_id=teacher_id, code='BM-' + secrets.token_urlsafe(24),
                            student_code='BMS-' + secrets.token_urlsafe(24), invited_by_id=invited_by_id)
    db.add(code)
    db.flush()
    return code


def inviter_for(db, value, role='teacher'):
    column = TeacherInviteCode.code if role == 'teacher' else TeacherInviteCode.student_code
    invitation = db.scalar(select(TeacherInviteCode).join(User, User.id == TeacherInviteCode.teacher_id)
                           .where(column == value.strip(), User.active == True, User.role == 'teacher')
                           .with_for_update(of=TeacherInviteCode))
    if not invitation:
        fail(403, 'INVITATION_REQUIRED', 'Enter a valid ' + ('teacher referral' if role == 'teacher' else 'student enrollment') + ' code shared by your teacher.')
    return invitation.teacher_id


def rotate_code(db, teacher_id, kind, current_code):
    invitation = db.scalar(select(TeacherInviteCode).where(TeacherInviteCode.teacher_id == teacher_id)
                           .with_for_update().execution_options(populate_existing=True))
    if not invitation:
        fail(503, 'INVITATION_NOT_CONFIGURED', 'Your class codes are not configured. Contact the administrator.')
    field = 'student_code' if kind == 'student' else 'code'
    if not secrets.compare_digest(getattr(invitation, field), current_code):
        fail(409, 'INVITATION_CHANGED', 'This code has already changed. Reload class codes before replacing it again.')
    setattr(invitation, field, ('BMS-' if kind == 'student' else 'BM-') + secrets.token_urlsafe(24))
    db.commit()
    return invitation
