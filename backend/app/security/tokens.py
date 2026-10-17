from datetime import datetime
import jwt


def encode_token(user_id: str, role: str, session_id: str, expiry: datetime, secret: str) -> str:
    return jwt.encode({'sub': user_id, 'role': role, 'sid': session_id, 'exp': expiry}, secret, algorithm='HS256')


def decode_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=['HS256'], options={'require': ['sub', 'role', 'sid', 'exp']})
