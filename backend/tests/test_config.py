from app.config import Settings


def test_host_debug_environment_does_not_configure_application(monkeypatch):
    monkeypatch.setenv('DEBUG', 'release')
    assert Settings(_env_file=None).debug is False
