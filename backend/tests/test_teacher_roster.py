import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models as m
from app.content.catalog import uid

pytestmark = pytest.mark.integration


def test_roster_pagination_search_and_assignment_scope(live_client, integration_engine):
    with Session(integration_engine) as db:
        teacher = db.get(m.User, uid('teacher_demo'))
        for name in ['roster_alpha', 'roster_beta', 'roster_literal_one']:
            user = m.User(username=name, password_hash=teacher.password_hash, role='learner')
            db.add(user); db.flush()
            db.add(m.TeacherAssignment(teacher_id=teacher.id, learner_id=user.id))
        outsider = m.User(username='roster_outside', password_hash=teacher.password_hash, role='learner')
        db.add(outsider); db.commit()
    assert live_client.post('/api/auth/login', json={'username':'teacher_demo','password':'integration-password-123'}).status_code == 200
    first = live_client.get('/api/teacher/roster?search=roster_&limit=2')
    assert first.status_code == 200
    first = first.json()['data']
    assert first['page']['total'] == 3 and first['page']['has_more']
    second = live_client.get('/api/teacher/roster?search=roster_&limit=2&offset=2').json()['data']
    assert len(second['learners']) == 1 and not second['page']['has_more']
    assert {u['username'] for u in first['learners'] + second['learners']} == {'roster_alpha','roster_beta','roster_literal_one'}
    exact = live_client.get('/api/teacher/roster?search=ROSTER_ALPHA').json()['data']
    assert [u['username'] for u in exact['learners']] == ['roster_alpha']
    assert live_client.get('/api/teacher/roster?search=%25').json()['data']['page']['total'] == 0
    assert live_client.get('/api/teacher/roster?limit=51').status_code == 422
    assert live_client.get('/api/teacher/roster?offset=-1').status_code == 422
    assert live_client.get('/api/teacher/roster?search='+'x'*33).status_code == 422
    live_client.post('/api/auth/login', json={'username':'learner_a','password':'integration-password-123'})
    assert live_client.get('/api/teacher/roster').status_code == 403


def test_roster_can_hide_demonstration_accounts(live_client):
    live_client.post('/api/auth/login', json={'username':'teacher_demo','password':'integration-password-123'})
    shown = live_client.get('/api/teacher/roster?search=learner_').json()['data']
    assert shown['page']['total'] >= 3
    hidden = live_client.get('/api/teacher/roster?search=learner_&include_samples=false').json()['data']
    assert hidden['learners'] == [] and hidden['page']['total'] == 0
