"""Rotation revokes future enrollment, never existing accounts or assignments."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models as m
from app.errors import AppError
from app.services.teacher_invites import create_code, inviter_for, rotate_code

pytestmark = pytest.mark.integration
PASSWORD = 'integration-password-123'


def teacher(client):
    client.post('/api/auth/login', json={'username':'teacher_demo','password':PASSWORD})
    return client.get('/api/teacher/invitation').json()['data']


def signup(client, role, code):
    name = 'rotate_' + uuid4().hex[:12]
    response = client.post('/api/auth/signup', json={'username':name,'password':PASSWORD,'role':role,'invite_code':code})
    return name, response


@pytest.mark.parametrize('kind,role,other', [('student','learner','teacher'), ('teacher','teacher','student')])
def test_rotation_revokes_old_code_preserves_reuse_and_existing_accounts(live_client, integration_engine, kind, role, other):
    old = teacher(live_client)
    name, created = signup(live_client, role, old[kind+'_code'])
    assert created.status_code == 201
    user_id = created.json()['data']['id']
    own_codes = live_client.get('/api/teacher/invitation').json()['data'] if role == 'teacher' else None
    teacher(live_client)
    changed = live_client.post('/api/teacher/invitation/rotate', json={'kind':kind,'current_code':old[kind+'_code']})
    assert changed.status_code == 200
    new = changed.json()['data']
    assert new[kind+'_code'] != old[kind+'_code']
    assert new[other+'_code'] == old[other+'_code']
    assert live_client.post('/api/teacher/invitation/rotate', json={'kind':kind,'current_code':old[kind+'_code']}).status_code == 409
    assert signup(live_client, role, old[kind+'_code'])[1].status_code == 403
    for _ in range(2):
        assert signup(live_client, role, new[kind+'_code'])[1].status_code == 201
    assert live_client.post('/api/auth/login', json={'username':name,'password':PASSWORD}).status_code == 200
    if role == 'learner':
        with Session(integration_engine) as db:
            assert db.scalar(select(m.TeacherAssignment).where(m.TeacherAssignment.learner_id == user_id)).teacher_id == old['teacher_id']
    else:
        assert live_client.get('/api/teacher/invitation').json()['data'] == own_codes


def test_rotation_requires_teacher_and_valid_kind(live_client):
    codes = teacher(live_client)
    assert live_client.post('/api/teacher/invitation/rotate', json={'kind':'both','current_code':codes['teacher_code']}).status_code == 422
    assert live_client.post('/api/teacher/invitation/rotate', json={'kind':'student'}).status_code == 422
    assert live_client.post('/api/teacher/invitation/rotate', json={'kind':'student','current_code':codes['student_code'],'teacher_id':str(uuid4())}).status_code == 422
    live_client.post('/api/auth/login', json={'username':'learner_a','password':PASSWORD})
    assert live_client.post('/api/teacher/invitation/rotate', json={'kind':'student','current_code':codes['student_code']}).status_code == 403


def test_concurrent_replacement_accepts_only_one_request(integration_engine):
    with Session(integration_engine) as db:
        owner = m.User(username='race_'+uuid4().hex[:12], role='teacher', password_hash='unused')
        db.add(owner); db.flush()
        invitation = create_code(db, owner.id)
        owner_id, old = owner.id, invitation.student_code
        db.commit()
    ready = Barrier(2)
    def replace():
        with Session(integration_engine) as db:
            ready.wait(timeout=5)
            try:
                rotate_code(db, owner_id, 'student', old)
            except AppError as error:
                return error.status
            return 200
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _:replace(), range(2)))
    assert sorted(results) == [200,409]


def test_signup_waits_for_rotation_and_rejects_replaced_code(integration_engine):
    # The pre-rotation lookup must recheck after PostgreSQL releases the row lock.
    with Session(integration_engine) as db:
        owner = m.User(username='lock_'+uuid4().hex[:12], role='teacher', password_hash='unused')
        db.add(owner); db.flush()
        invitation = create_code(db, owner.id)
        old = invitation.student_code
        invitation_id = invitation.id
        db.commit()
    started = Event()
    def resolve_old():
        with Session(integration_engine) as db:
            started.set()
            try:
                inviter_for(db, old, 'learner')
            except AppError as error:
                return error.status
            return 200
    with Session(integration_engine) as changing, ThreadPoolExecutor(max_workers=1) as pool:
        locked = changing.scalar(select(m.TeacherInviteCode).where(m.TeacherInviteCode.id == invitation_id).with_for_update())
        locked.student_code = 'BMS-' + uuid4().hex
        changing.flush()
        pending = pool.submit(resolve_old)
        assert started.wait(5)
        # A bounded wait proves the resolver cannot accept a code while rotation is uncommitted.
        from concurrent.futures import TimeoutError
        with pytest.raises(TimeoutError):
            pending.result(timeout=0.3)
        changing.commit()
        assert pending.result(timeout=10) == 403
