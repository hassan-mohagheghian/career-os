"""Tests for SQLAlchemyPendingCompanyRepository — atomic claim, reset_steps with keep_status."""

import pytest
from sqlalchemy.orm import sessionmaker

from shared.infrastructure.database.sqlalchemy_config import Base
from companies.infrastructure.models.company_model import CompanyModel
from companies.infrastructure.repositories.sa_pending_company_repository import SQLAlchemyPendingCompanyRepository


@pytest.fixture
def db(_engine):
    connection = _engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _insert_company(session, text='TestCorp', status='queued'):
    m = CompanyModel(name=text, status=status, source='web')
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


class TestPickQueuedItem:
    """Test atomic pick_queued_item uses SELECT + conditional UPDATE."""

    def test_pick_company(self, db):
        repo = SQLAlchemyPendingCompanyRepository(db)
        cid = _insert_company(db, 'CorpA', 'queued')

        result = repo.pick_queued_item('pending_companies')
        assert result is not None
        assert result['id'] == cid
        assert result['status'] == 'processing'

    def test_pick_company_returns_none_when_empty(self, db):
        repo = SQLAlchemyPendingCompanyRepository(db)
        result = repo.pick_queued_item('pending_companies')
        assert result is None


class TestResetSteps:
    """Test reset_steps with keep_status parameter."""

    def test_reset_steps_company(self, db):
        repo = SQLAlchemyPendingCompanyRepository(db)
        cid = _insert_company(db, 'Corp', 'starting')
        db.query(CompanyModel).filter(CompanyModel.id == cid).first()
        db.commit()

        repo.reset_steps(cid, version=1, table='pending_companies')

        row = db.query(CompanyModel).filter(CompanyModel.id == cid).first()
        assert row.status == 'created'

    def test_reset_steps_company_keep_status(self, db):
        repo = SQLAlchemyPendingCompanyRepository(db)
        cid = _insert_company(db, 'Corp', 'starting')
        db.query(CompanyModel).filter(CompanyModel.id == cid).first()
        db.commit()

        repo.reset_steps(cid, version=1, table='pending_companies', keep_status=True)

        row = db.query(CompanyModel).filter(CompanyModel.id == cid).first()
        assert row.status == 'starting'
