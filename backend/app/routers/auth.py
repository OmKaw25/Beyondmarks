from datetime import timedelta
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_db
from app.errors import fail
from app.models import AuthSession, LearnerProfile, TeacherAssignment, User, now
from app.schemas import Signup, Login
from app.security.dependencies import get_current_user
from app.security.hashing import hash_password, verify_password
from app.security.tokens import encode_token
from app.services.teacher_invites import create_code, inviter_for

router = APIRouter(prefix='/api/auth', tags=['auth'])


def public_user(user):
    return dict(id=user.id, username=user.username, role=user.role, is_synthetic=user.is_synthetic)


def require_secret():
    settings = get_settings()
    if len(settings.jwt_secret) < 32:
        fail(503, 'AUTH_CONFIGURATION', 'Authentication needs a locally configured JWT secret of at least 32 characters.')
    return settings


def create_session(db, user, response):
    settings = require_secret()
    expiry = now() + timedelta(minutes=settings.jwt_expire_minutes)
    session = AuthSession(user_id=user.id, expires_at=expiry)
    db.add(session); db.flush()
    token = encode_token(user.id, user.role, session.id, expiry, settings.jwt_secret)
    db.commit()
    response.set_cookie('bm_session', token, httponly=True, secure=settings.secure_cookies,
                        samesite='lax', max_age=settings.jwt_expire_minutes * 60, path='/')
    response.headers['Cache-Control'] = 'no-store'
    return {'data': public_user(user)}


@router.post('/signup', status_code=201)
def signup(payload: Signup, response: Response, db: Session = Depends(get_db)):
    require_secret()
    inviter_id = inviter_for(db, payload.invite_code, payload.role)
    if db.scalar(select(User).where(User.username == payload.username)):
        fail(409, 'USERNAME_TAKEN', 'This username is already in use.')
    user = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    try:
        db.flush()
        if user.role == 'learner':
            db.add(LearnerProfile(user_id=user.id, display_name=user.username))
            db.add(TeacherAssignment(teacher_id=inviter_id, learner_id=user.id))
        else:
            create_code(db, user.id, inviter_id)
            from app.services.classroom import ensure_programming
            ensure_programming(db,user.id)
        return create_session(db, user, response)
    except IntegrityError:
        db.rollback()
        fail(409, 'USERNAME_TAKEN', 'This username is already in use.')


@router.post('/login')
def login(payload: Login, response: Response, db: Session = Depends(get_db)):
    require_secret()
    user = db.scalar(select(User).where(User.username == payload.username))
    # Use a valid fixed bcrypt hash to reduce username-dependent hashing work.
    dummy = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxO4g4mQpfQ9fTKQz2uJyRGSY7W'
    valid = verify_password(payload.password, user.password_hash if user else dummy)
    if not user or not valid:
        fail(401, 'INVALID_CREDENTIALS', 'Username or password is incorrect.')
    if not user.active:
        fail(403, 'ACCOUNT_DISABLED', 'This account is disabled.')
    return create_session(db, user, response)


@router.get('/me')
def me(user: User = Depends(get_current_user)):
    return {'data': public_user(user)}


@router.post('/logout')
def logout(request: Request, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.get(AuthSession, request.state.session_id)
    session.revoked = True
    db.commit()
    response.delete_cookie('bm_session', path='/')
    return {'data': {'signed_out': True}}
