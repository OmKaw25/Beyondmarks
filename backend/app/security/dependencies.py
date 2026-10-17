from datetime import datetime, timezone
from uuid import UUID
import jwt
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_db
from app.errors import fail
from app.models import User, AuthSession
from app.security.tokens import decode_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get('bm_session')
    if not token:
        fail(401, 'SIGN_IN_REQUIRED', 'Please sign in to continue.')
    try:
        claims = decode_token(token, get_settings().jwt_secret)
        UUID(claims['sub']); UUID(claims['sid'])
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        fail(401, 'SESSION_EXPIRED', 'Your session has expired. Please sign in again.')
    session = db.get(AuthSession, claims['sid'])
    user = db.get(User, claims['sub'])
    if not session or session.revoked or session.expires_at <= datetime.now(timezone.utc) or session.user_id != claims['sub']:
        fail(401, 'SESSION_EXPIRED', 'Your session has expired. Please sign in again.')
    if not user or not user.active:
        fail(403, 'ACCOUNT_DISABLED', 'This account is disabled.')
    request.state.user_id = user.id
    request.state.session_id = session.id
    return user


def require_learner(user: User = Depends(get_current_user)) -> User:
    if user.role != 'learner':
        fail(403, 'LEARNER_REQUIRED', 'This page is available to learner accounts.')
    return user


def require_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role != 'teacher':
        fail(403, 'TEACHER_REQUIRED', 'Teacher access is required.')
    return user
