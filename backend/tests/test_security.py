from datetime import datetime, timedelta, timezone
import jwt
import pytest
from pydantic import ValidationError
from app.schemas import Signup, Correction
from app.security.tokens import encode_token, decode_token
from app.security.hashing import hash_password, verify_password


def test_bcrypt_verifies_and_never_stores_plaintext():
    value = hash_password('long-test-password')
    assert value.startswith('$2')
    assert verify_password('long-test-password', value)
    assert not verify_password('incorrect', value)
    assert not verify_password('x' * 73, value)


def test_username_normalization_password_bytes_and_extra_fields():
    assert Signup(username='Learner_A', password='long-test-password').username == 'learner_a'
    with pytest.raises(ValidationError):
        Signup(username='ab', password='short')
    with pytest.raises(ValidationError):
        Signup(username='learner', password='é' * 37)
    with pytest.raises(ValidationError):
        Signup(username='learner', password='long-test-password', elevated=True)


def test_jwt_checks_expiry_signature_and_required_claims():
    secret = 'a-secure-test-key-only-for-unit-tests-12345'
    token = encode_token('user', 'learner', 'session', datetime.now(timezone.utc) + timedelta(minutes=5), secret)
    assert decode_token(token, secret)['sid'] == 'session'
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, 'different-key-at-least-thirty-two-characters')
    expired = encode_token('user', 'learner', 'session', datetime.now(timezone.utc) - timedelta(minutes=1), secret)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired, secret)


def test_correction_requires_reasoning():
    with pytest.raises(ValidationError):
        Correction(segment_ids=[], broad_category='Concept', specific_reason='loop', explanation='')
