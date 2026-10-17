"""Schema-scoped maintenance. Session cleanup previews by default; --apply commits."""
import argparse
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from app import models as m
from app.config import get_settings
from app.db import engine_for


def cleanup_sessions(db, *, apply=False):
    expired=m.AuthSession.expires_at <= m.now()
    count=db.scalar(select(func.count()).select_from(m.AuthSession).where(expired))
    if apply: db.execute(delete(m.AuthSession).where(expired))
    return count


def mark_demo_accounts(db, usernames):
    """Explicit names only: flag automated accounts and their existing activity."""
    users=list(db.scalars(select(m.User).where(m.User.username.in_(usernames))))
    if {u.username for u in users} != set(usernames):
        raise ValueError('Every requested username must exist; no accounts were changed.')
    from sqlalchemy import update
    ids=[u.id for u in users]
    for user in users: user.is_synthetic=True;user.data_origin='demo'
    db.execute(update(m.Attempt).where(m.Attempt.learner_id.in_(ids)).values(is_synthetic=True))
    db.execute(update(m.RetentionCheck).where(m.RetentionCheck.learner_id.in_(ids)).values(is_synthetic=True))
    return len(users)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['cleanup-sessions','rebuild-progress','mark-demo'])
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--username',action='append',default=[])
    args=parser.parse_args();settings=get_settings()
    with Session(engine_for(settings.database_url,settings.database_schema)) as db:
        if args.operation=='cleanup-sessions': count=cleanup_sessions(db,apply=args.apply)
        elif args.operation=='mark-demo':
            if not args.username: parser.error('mark-demo requires explicit --username values.')
            count=mark_demo_accounts(db,args.username)
        else:
            from app.services.classroom import refresh_course_progress
            ids=list(db.scalars(select(m.QuizSubmission.learner_id).distinct()))
            for learner_id in ids: refresh_course_progress(db,learner_id)
            count=len(ids)
        if args.apply: db.commit()
        else: db.rollback()
    print(f'{args.operation}: {count} records; {"applied" if args.apply else "preview only"}; schema={settings.database_schema}.')


if __name__ == '__main__': main()
