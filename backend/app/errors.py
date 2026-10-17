class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details=None):
        self.status, self.code, self.message = status, code, message
        self.details = details or {}


def fail(status, code, message):
    raise AppError(status, code, message)
