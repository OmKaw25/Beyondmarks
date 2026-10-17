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
                           .where(column == value.strip(), User.active == True, User.role == 'teacher'))
    if not invitation:
        fail(403, 'INVITATION_REQUIRED', 'Enter a valid ' + ('teacher referral' if role == 'teacher' else 'student enrollment') + ' code shared by your teacher.')
    return invitation.teacher_id
