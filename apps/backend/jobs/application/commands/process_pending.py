import json
import os
from datetime import datetime

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

_file_dir = os.path.dirname(os.path.abspath(__file__))
_db_path = os.environ.get('DB_PATH', os.path.join(_file_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_file_dir, _db_path)

import sys
sys.path.insert(0, os.path.join(_file_dir, '..'))
from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.database.sqlalchemy_config import Base

log = get_logger('jobs.commands.process_pending')
import jobs.infrastructure.models.job_model
import shared.infrastructure.database.models.misc_models
from jobs.infrastructure.models.job_model import JobModel
from shared.infrastructure.database.models.misc_models import SummaryModel, ResumeModel


def get_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    return Session(), engine


def update_step(session, job_num, step, value, status=None, company=None, job_num_field=None, error=None):
    m = session.query(JobModel).filter(JobModel.num == job_num).first()
    if not m:
        return
    if hasattr(m, step):
        setattr(m, step, value)
    if status:
        m.status = status
    if company:
        m.company = company
    if error:
        m.error = error
    m.updated_at = datetime.now().isoformat()
    session.commit()


def get_pending(session):
    rows = session.query(JobModel).filter(
        JobModel.deleted == 0,
        ~JobModel.status.in_(['completed', 'failed'])
    ).order_by(JobModel.created_at.asc()).all()
    return [{'id': r.num, 'url': r.url or '', 'source': r.source or '', 'status': r.status} for r in rows]


def add_job(session, data):
    m = session.query(JobModel).filter(JobModel.num == data['num']).first()
    if m:
        for k, v in data.items():
            if hasattr(m, k):
                setattr(m, k, v)
    else:
        m = JobModel(num=data['num'], company=data.get('company'), role=data.get('role'),
                     location=data.get('location'), match=data.get('match'), score=data.get('score'),
                     salary=data.get('salary'), stack=data.get('stack'), visa=data.get('visa'),
                     url=data.get('url'))
        session.add(m)
    session.commit()


def add_summary(session, data):
    m = session.query(SummaryModel).filter(SummaryModel.num == data['num']).first()
    if m:
        m.company = data.get('company')
        m.summary = data.get('summary')
    else:
        m = SummaryModel(num=data['num'], company=data.get('company'), summary=data.get('summary'))
        session.add(m)
    session.commit()


def get_next_job_num(session):
    max_num = session.query(func.max(JobModel.num)).scalar()
    return (max_num or 0) + 1


if __name__ == '__main__':
    session, engine = get_session()
    try:
        pending = get_pending(session)
        log.info('Pending jobs', count=len(pending))
        for p in pending:
            log.info('  pending item', id=p['id'], source=p['source'], status=p['status'], url=p['url'][:60])
    finally:
        session.close()
        engine.dispose()
