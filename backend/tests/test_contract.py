from app.main import app


def test_full_prd_api_contract_is_registered():
    paths = app.openapi()['paths']
    required = ['/api/learner/home', '/api/investigations/start', '/api/investigations/{attempt_id}',
                '/api/investigations/{attempt_id}/correction', '/api/investigations/{attempt_id}/diagnosis',
                '/api/investigations/{attempt_id}/challenge', '/api/investigations/{attempt_id}/select-follow-up',
                '/api/investigations/{attempt_id}/follow-up', '/api/investigations/{attempt_id}/support',
                '/api/investigations/{attempt_id}/transfer', '/api/investigations/{attempt_id}/independent',
                '/api/retention', '/api/retention/{check_id}/adapt', '/api/teacher/learners',
                '/api/teacher/learners/{learner_id}', '/api/teacher/learners/{learner_id}/timeline']
    assert set(required) <= set(paths)
