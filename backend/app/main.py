import logging
from uuid import uuid4
from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_db
from app.errors import AppError
from app.routers import auth, learning, teacher, classroom
from app.routers import learning_evidence

app = FastAPI(title='Beyond Marks API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=get_settings().origins, allow_credentials=True,
                   allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])
log = logging.getLogger('beyond-marks')


def error_response(status, code, message, details=None):
    return JSONResponse(status_code=status, content={'error': {'code': code, 'message': message, 'details': details or {}}})


@app.middleware('http')
async def request_guard(request: Request, call_next):
    request_id = str(uuid4())
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        if origin and origin not in get_settings().origins:
            return error_response(403, 'ORIGIN_REJECTED', 'This request came from an untrusted origin.')
    response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    log.info('request_id=%s method=%s route=%s status=%s', request_id, request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(AppError)
async def application_error(request, exc):
    return error_response(exc.status, exc.code, exc.message, exc.details)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Do not echo Pydantic's input field: it can contain passwords and invitation codes.
    details = [{'field': '.'.join(str(p) for p in e['loc']), 'message': e['msg']} for e in exc.errors()]
    return error_response(422, 'VALIDATION_ERROR', 'Please check the highlighted fields.', details)


@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    log.error('database_operation_failed type=%s', type(exc).__name__)
    return error_response(503, 'DATABASE_UNAVAILABLE', 'The learning database is unavailable. Check its connection and migrations, then try again.')


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    log.error('unexpected_error type=%s', type(exc).__name__)
    return error_response(500, 'INTERNAL_ERROR', 'Something went wrong. Please try again.')


@app.get('/api/health')
def health():
    return {'data': {'status': 'ok', 'database_configured': bool(get_settings().database_url)}}


@app.get('/api/ready')
def ready(db: Session = Depends(get_db)):
    db.execute(text('SELECT 1'))
    return {'data': {'status': 'ready'}}


app.include_router(auth.router)
app.include_router(learning.router)
app.include_router(teacher.router)
app.include_router(classroom.router)
app.include_router(learning_evidence.router)
