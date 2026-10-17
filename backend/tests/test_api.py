from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings


def test_health_and_missing_database_are_explicit(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', '')
    get_settings.cache_clear()
    with TestClient(app) as client:
        assert client.get('/api/health').json()['data']['status'] == 'ok'
        response = client.get('/api/ready')
        assert response.status_code == 503
        assert response.json()['error']['code'] == 'DATABASE_NOT_CONFIGURED'
        assert 'password' not in response.text.lower()
    get_settings.cache_clear()


def test_mutations_reject_untrusted_origin():
    with TestClient(app) as client:
        response = client.post('/api/auth/login', headers={'Origin':'https://untrusted.invalid'}, json={'username':'learner','password':'long-enough-password'})
        assert response.status_code == 403
