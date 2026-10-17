"""Create an isolated pilot or synthetic showcase; never reset an existing schema.

Run from backend: python -m app.bootstrap --schema bm_pilot_2026 --teacher om_teacher --output ../.env.pilot
Showcase: python -m app.bootstrap --schema bm_showcase_2026 --demo --output ../.env.showcase
The output is a local secret dotenv file. No passwords or invitation codes are printed.
"""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
from alembic import command
from alembic.config import Config
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from app import models as m
from app.config import ROOT, Settings, get_settings
from app.db import engine_for
from app.seed import bootstrap_teacher, seed, seed_curriculum


def write_private_env(path, values):
    path=Path(path).resolve()
    if not path.name.startswith('.env.'):
        raise ValueError('Credential output must be named .env.<name> so repository ignore rules protect it.')
    descriptor=os.open(path,os.O_WRONLY | os.O_CREAT | os.O_EXCL,0o600)
    try:
        if os.name == 'nt':
            account=subprocess.check_output(['whoami'],text=True).strip()
            subprocess.run(['icacls',str(path),'/inheritance:r','/grant:r',account+':F'],
                           check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        with os.fdopen(descriptor,'w',encoding='utf-8') as handle:
            descriptor=None
            handle.write('# Local credentials. Never commit or share this file.\n')
            handle.writelines(f'{key}={json.dumps(str(value))}\n' for key,value in values.items())
    finally:
        if descriptor is not None: os.close(descriptor)
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schema',required=True)
    parser.add_argument('--teacher',default='pilot_teacher')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--demo',action='store_true',help='Create explicitly synthetic demo accounts and labelled history.')
    args=parser.parse_args()
    schema=Settings.safe_database_schema(args.schema)
    if schema == 'public': parser.error('Bootstrap requires a new named schema; public is never changed.')
    if not re.fullmatch(r'[A-Za-z0-9_]{3,32}',args.teacher): parser.error('Teacher username must be 3–32 letters, numbers or underscores.')
    if args.output.exists() or not args.output.name.startswith('.env.'):
        parser.error('Use a new .env.<name> output path; existing credentials are never overwritten.')
    settings=get_settings()
    password=secrets.token_urlsafe(24)
    # CREATE (without IF NOT EXISTS) intentionally refuses reuse of any existing data.
    with engine_for(settings.database_url,'public').begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    os.environ['APP_DATABASE_SCHEMA']=schema
    get_settings.cache_clear()
    config=Config(str(ROOT/'backend'/'alembic.ini'))
    config.set_main_option('script_location',str(ROOT/'backend'/'alembic'))
    command.upgrade(config,'head')
    with Session(engine_for(settings.database_url,schema),expire_on_commit=False) as db:
        if args.demo:
            seed(db,password)
            teacher=db.scalar(select(m.User).where(m.User.username=='teacher_demo'))
            invitation=db.scalar(select(m.TeacherInviteCode).where(m.TeacherInviteCode.teacher_id==teacher.id))
        else:
            seed_curriculum(db)
            teacher,invitation=bootstrap_teacher(db,args.teacher,password)
        output=write_private_env(args.output,dict(DATABASE_URL=settings.database_url,APP_DATABASE_SCHEMA=schema,
            JWT_SECRET=secrets.token_urlsafe(48),CORS_ORIGINS='http://localhost:3001,http://127.0.0.1:3001',
            GEMINI_API_KEY=settings.gemini_api_key,GEMINI_MODEL=settings.gemini_model,
            DEMO_PASSWORD=password if args.demo else '',BOOTSTRAP_TEACHER_USERNAME=teacher.username,
            BOOTSTRAP_TEACHER_PASSWORD=password,BOOTSTRAP_TEACHER_CODE=invitation.code,
            BOOTSTRAP_STUDENT_CODE=invitation.student_code))
        db.commit()
    print(f'Created {"synthetic showcase" if args.demo else "clean pilot"} schema {schema}. Local credentials: {output}')


if __name__ == '__main__': main()
