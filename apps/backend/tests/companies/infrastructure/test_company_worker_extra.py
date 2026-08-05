"""Additional coverage for company_worker.py — legacy helpers, save, rules, LangGraph worker."""
import json
from unittest.mock import patch, MagicMock

import pytest

from companies.infrastructure.models.company_model import CompanyModel, CompanyIntelligenceModel
from rules.infrastructure.models.rule_model import RuleModel


def _insert_company(session, name='Acme', status='processing', **kw):
    m = CompanyModel(name=name, source='web', status=status, **kw)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


def _make_worker():
    from companies.infrastructure.workers.company_worker import CompanyWorker
    repo = MagicMock()
    return CompanyWorker(repo, MagicMock(), MagicMock(), MagicMock(), MagicMock(), llm_service=None)


class TestCompanyHelpers:
    def test_mark_calls_update_step(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _mark
        with patch('companies.infrastructure.workers.company_worker._update_step') as mock_update:
            _mark(1, 'step_fetch')
        mock_update.assert_called_once_with(1, 'step_fetch', 1)

    def test_save_session_id(self, mock_get_session_company_worker):
        cid = _insert_company(mock_get_session_company_worker)
        from companies.infrastructure.workers.company_worker import _save_session_id
        broadcaster = MagicMock()
        with patch('companies.infrastructure.workers.company_worker.broadcaster', broadcaster):
            _save_session_id(cid, 'sess_1')
        row = mock_get_session_company_worker.query(CompanyModel).filter(CompanyModel.id == cid).first()
        assert row.session_id == 'sess_1'
        broadcaster.step_update.assert_called_once()

    def test_save_session_id_missing_row(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _save_session_id
        with patch('companies.infrastructure.workers.company_worker.broadcaster'):
            _save_session_id(99999, 'sess_1')

    def test_log_missing_row_still_broadcasts(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _log
        broadcaster = MagicMock()
        with patch('companies.infrastructure.workers.company_worker.broadcaster', broadcaster):
            _log(99999, 'fetch', 'msg')
        broadcaster.log.assert_called_once()


class TestCompanyFetchUrl:
    def test_fetch_url_ok(self):
        from companies.infrastructure.workers.company_worker import _fetch_url
        page = MagicMock()
        page.is_ok = True
        page.plain_text = 'company text'
        with patch('companies.infrastructure.workers.company_worker.fetch_page', return_value=page):
            assert _fetch_url('https://acme.com') == 'company text'

    def test_fetch_url_raises(self):
        from companies.infrastructure.workers.company_worker import _fetch_url
        page = MagicMock()
        page.is_ok = False
        page.error.message = 'Connection refused'
        with patch('companies.infrastructure.workers.company_worker.fetch_page', return_value=page), \
             pytest.raises(RuntimeError, match='Connection refused'):
            _fetch_url('https://acme.com')


class TestExtractCompanyInfo:
    @pytest.mark.parametrize('input_type,content_prefix', [
        ('multi_note', 'note content'),
        ('manual', 'manual content'),
        ('url', 'URL: https://acme.com'),
    ])
    def test_extract_success(self, mock_get_session_company_worker, input_type, content_prefix):
        from companies.infrastructure.workers.company_worker import _extract_company_info
        llm = MagicMock()
        llm.generate_structured.return_value.content = '{"name": "Acme"}'
        with patch('companies.infrastructure.workers.company_worker.get_llm_service', return_value=llm), \
             patch('companies.infrastructure.workers.company_worker.load_prompt', return_value='p'):
            result = _extract_company_info('https://acme.com', input_type, 1)
        assert result == {'name': 'Acme'}

    def test_extract_failure_logs_and_returns_none(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _extract_company_info
        llm = MagicMock()
        llm.generate_structured.side_effect = RuntimeError('llm down')
        with patch('companies.infrastructure.workers.company_worker.get_llm_service', return_value=llm), \
             patch('companies.infrastructure.workers.company_worker.load_prompt', return_value='p'), \
             patch('companies.infrastructure.workers.company_worker._log') as mock_log:
            result = _extract_company_info('text', 'manual', 1)
        assert result is None
        mock_log.assert_called_once()


class TestLoadRules:
    def test_company_context_unknown_type(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _load_rules
        from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
        sa_session = mock_get_session_company_worker
        sa_session.add(RuleModel(category='culture', rule_type='company', scope='COMPANY_PRODUCT',
                                 key='perks', value='Strong', priority=5))
        sa_session.commit()
        with patch('companies.infrastructure.workers.company_worker.SQLAlchemyRuleRepository', SQLAlchemyRuleRepository, create=True):
            result = _load_rules(context='company', company_type='UNKNOWN')
        assert 'perks' in result

    def test_company_context_recruiting(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _load_rules
        from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
        sa_session = mock_get_session_company_worker
        sa_session.add(RuleModel(category='recruit', rule_type='company', scope='COMPANY_RECRUITING',
                                 key='headhunt', value='Yes', priority=1))
        sa_session.commit()
        with patch('companies.infrastructure.workers.company_worker.SQLAlchemyRuleRepository', SQLAlchemyRuleRepository, create=True):
            result = _load_rules(context='company', company_type='RECRUITING_AGENCY')
        assert 'headhunt' in result

    def test_job_context(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _load_rules
        from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
        sa_session = mock_get_session_company_worker
        sa_session.add(RuleModel(category='fit', rule_type='job', scope='JOB',
                                 key='python', value='High', priority=10))
        sa_session.commit()
        with patch('companies.infrastructure.workers.company_worker.SQLAlchemyRuleRepository', SQLAlchemyRuleRepository, create=True):
            result = _load_rules(context='job')
        assert 'python' in result

    def test_no_rules(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _load_rules
        from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
        with patch('companies.infrastructure.workers.company_worker.SQLAlchemyRuleRepository', SQLAlchemyRuleRepository, create=True):
            assert _load_rules(context='company', company_type='PRODUCT_COMPANY') == 'No scoring rules set.'

    def test_rules_use_priority_as_weight(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _load_rules
        from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
        sa_session = mock_get_session_company_worker
        sa_session.add(RuleModel(category='cat', rule_type='company', scope='COMPANY_RECRUITING',
                                 key='k1', value='v1', priority=5))
        sa_session.add(RuleModel(category='cat', rule_type='company', scope='COMPANY_RECRUITING',
                                 key='k2', value='v2', priority=3))
        sa_session.commit()
        with patch('companies.infrastructure.workers.company_worker.SQLAlchemyRuleRepository', SQLAlchemyRuleRepository, create=True):
            result = _load_rules(context='company', company_type='STAFFING_COMPANY')
        assert 'weight:5' in result
        assert 'weight:3' in result


class TestAnalyzeCompany:
    def test_analyze_success(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _analyze_company
        llm = MagicMock()
        llm.generate_structured.return_value.content = '{"scores": {"a": 1}}'
        with patch('companies.infrastructure.workers.company_worker.get_llm_service', return_value=llm), \
             patch('companies.infrastructure.workers.company_worker.load_prompt', return_value='p'), \
             patch('companies.infrastructure.workers.company_worker._load_rules', return_value='rules'):
            result = _analyze_company({'name': 'Acme'}, 1, company_type='UNKNOWN')
        assert result == {'scores': {'a': 1}}

    def test_analyze_failure_returns_none(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _analyze_company
        llm = MagicMock()
        llm.generate_structured.side_effect = ValueError('bad')
        with patch('companies.infrastructure.workers.company_worker.get_llm_service', return_value=llm), \
             patch('companies.infrastructure.workers.company_worker.load_prompt', return_value='p'), \
             patch('companies.infrastructure.workers.company_worker._load_rules', return_value='rules'):
            assert _analyze_company({'name': 'Acme'}, 1) is None


class TestSaveCompany:
    def test_save_existing_company(self, mock_get_session_company_worker):
        cid = _insert_company(mock_get_session_company_worker, name='OldName')
        from companies.infrastructure.workers.company_worker import _save_company
        company_data = {'name': 'NewName', 'website': 'https://new.com', 'domain': 'new.com',
                        'industry': 'AI', 'country': 'DE', 'city': 'Berlin',
                        'description': 'desc', 'company_size': '50', 'company_type': 'PRODUCT_COMPANY',
                        'logo_url': '', 'founded_year': '2010', 'headquarters_full': 'Berlin',
                        'countries_of_operation': ['DE'], 'funding_stage': 'Seed',
                        'funding_amount': '1m', 'products': [{'name': 'x'}],
                        'tech_stack': {'langs': ['Python']}, 'work_environment': {'office': True},
                        'key_clients': ['a'], 'competitors': ['b'], 'investors': ['c'],
                        'contact_info': {'email': 'x@y.com'}, 'engineering_culture': {},
                        'culture_signals': {}, 'international_signals': {}, 'benefits': {},
                        'extra': {}}
        intel = {'scores': {'fit': 80}, 'overview': {'o': 1}}
        result = _save_company(company_data, intel, 'raw source text', pending_company_id=cid)
        assert result == cid
        row = mock_get_session_company_worker.query(CompanyModel).filter(CompanyModel.id == cid).first()
        assert row.name == 'NewName'
        assert row.website == 'https://new.com'
        intel_row = mock_get_session_company_worker.query(CompanyIntelligenceModel).filter(
            CompanyIntelligenceModel.company_id == cid).first()
        assert intel_row is not None
        assert json.loads(intel_row.scores) == {'fit': 80}

    def test_save_pending_id_missing_inserts_new(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _save_company
        company_data = {'name': 'FreshCo', 'website': '', 'domain': '', 'industry': '',
                        'country': '', 'city': '', 'description': '', 'company_size': '',
                        'company_type': '', 'logo_url': '', 'founded_year': '',
                        'headquarters_full': '', 'countries_of_operation': [],
                        'funding_stage': '', 'funding_amount': '', 'products': [],
                        'tech_stack': {}, 'work_environment': {}, 'extra': {}}
        result = _save_company(company_data, {'scores': {}}, None, pending_company_id=99999)
        assert isinstance(result, int)
        row = mock_get_session_company_worker.query(CompanyModel).filter(CompanyModel.id == result).first()
        assert row.name == 'FreshCo'
        intel_row = mock_get_session_company_worker.query(CompanyIntelligenceModel).filter(
            CompanyIntelligenceModel.company_id == result).first()
        assert intel_row is not None

    def test_save_no_company_id_inserts(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import _save_company
        company_data = {'name': 'NoIdCo', 'website': '', 'domain': '', 'industry': '',
                        'country': '', 'city': '', 'description': '', 'company_size': '',
                        'company_type': '', 'logo_url': '', 'founded_year': '',
                        'headquarters_full': '', 'countries_of_operation': [],
                        'funding_stage': '', 'funding_amount': '', 'products': [],
                        'tech_stack': {}, 'work_environment': {}, 'extra': {}}
        result = _save_company(company_data, {'scores': {'x': 1}}, '')
        assert isinstance(result, int)
        row = mock_get_session_company_worker.query(CompanyModel).filter(CompanyModel.id == result).first()
        assert row.name == 'NoIdCo'


class TestProcessCompany:
    def test_process_company_delegates(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import process_company
        with patch('companies.infrastructure.workers.company_worker.CompanyWorker') as MockWorker, \
             patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            process_company(123)
        MockWorker.return_value.process.assert_called_once_with(123)
        mock_qm.return_value.signal_job_done.assert_called_once_with(123)

    def test_process_company_signal_failure_swallowed(self, mock_get_session_company_worker):
        from companies.infrastructure.workers.company_worker import process_company
        with patch('companies.infrastructure.workers.company_worker.CompanyWorker') as MockWorker, \
             patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.side_effect = RuntimeError('no queue')
            process_company(123)
        MockWorker.return_value.process.assert_called_once_with(123)


class TestCompanyWorkerOop:
    def test_table_property(self):
        assert _make_worker().table == 'company'

    def test_pipeline_steps_empty(self):
        assert _make_worker().pipeline_steps == []

    def test_reset_steps(self):
        worker = _make_worker()
        worker._reset_steps(5)
        worker._pending_repo.update_status.assert_called_once_with(5, 'processing', workflow_log='[]')

    def test_get_graph_caches(self):
        from companies.infrastructure.workers.company_worker import CompanyWorker
        worker = _make_worker()
        builder = MagicMock()
        with patch('companies.infrastructure.workers.company_worker.build_company_processing_graph',
                   return_value=builder):
            g1 = worker._get_graph()
            g2 = worker._get_graph()
        assert g1 is g2
        builder.compile.assert_called_once()

    def test_update_node_status_known(self):
        worker = _make_worker()
        worker._update_node_status(5, 'fetch_content')
        worker._pending_repo.update_status.assert_called_once_with(
            5, 'processing', current_node='fetch_content')

    def test_update_node_status_unknown(self):
        worker = _make_worker()
        with patch.object(worker, '_log') as mock_log:
            worker._update_node_status(5, 'mystery_node')
        worker._pending_repo.update_status.assert_not_called()
        mock_log.assert_not_called()

    def test_execute_pipeline_success(self):
        from companies.infrastructure.workers.company_worker import CompanyWorker
        worker = _make_worker()
        item = {
            'notes': json.dumps([{'type': 'text', 'content': 'manual note'}]),
            'links': json.dumps([{'url': 'https://link.com'}]),
            'company_id': 10,
            'source': 'web',
        }
        result_dict = {
            'progress': {'completed_nodes': ['load_context', 'fetch_content', 'save_results']},
            'errors': [],
            'failure_details': [],
            'metadata': {'persistence': {'success': True, 'company_id': 10, 'company_name': 'Acme'}},
        }
        with patch('companies.infrastructure.workers.company_worker.create_initial_state',
                   return_value={'input': ''}), \
             patch.object(worker, '_get_graph', return_value=MagicMock(invoke=MagicMock(return_value=result_dict))):
            result = worker._execute_pipeline(5, item)
        assert result == {'company_id': 10, 'name': 'Acme'}

    def test_execute_pipeline_no_notes_builds_from_input_url(self):
        from companies.infrastructure.workers.company_worker import CompanyWorker
        worker = _make_worker()
        item = {'notes': 'bad json {{', 'links': 'bad json {{', 'input_text': 'https://acme.com'}
        result_dict = {
            'progress': {'completed_nodes': []},
            'errors': [],
            'failure_details': [],
            'metadata': {'persistence': {'success': True, 'company_id': 1, 'company_name': 'X'}},
        }
        with patch('companies.infrastructure.workers.company_worker.create_initial_state') as mock_init, \
             patch.object(worker, '_get_graph', return_value=MagicMock(invoke=MagicMock(return_value=result_dict))):
            worker._execute_pipeline(5, item)
        _, kwargs = mock_init.call_args
        assert '"type": "url"' in kwargs['context']['notes']

    def test_execute_pipeline_no_notes_text_input(self):
        from companies.infrastructure.workers.company_worker import CompanyWorker
        worker = _make_worker()
        item = {'input_text': 'plain text company'}
        result_dict = {
            'progress': {'completed_nodes': []},
            'errors': [],
            'failure_details': [],
            'metadata': {'persistence': {'success': True, 'company_id': 1, 'company_name': 'X'}},
        }
        with patch('companies.infrastructure.workers.company_worker.create_initial_state') as mock_init, \
             patch.object(worker, '_get_graph', return_value=MagicMock(invoke=MagicMock(return_value=result_dict))):
            worker._execute_pipeline(5, item)
        _, kwargs = mock_init.call_args
        assert '"type": "text"' in kwargs['context']['notes']

    def test_execute_pipeline_errors_raise(self):
        from companies.infrastructure.workers.company_worker import CompanyWorker
        worker = _make_worker()
        item = {'notes': '[]', 'links': '[]', 'input_text': 'text'}
        result_dict = {
            'progress': {'completed_nodes': []},
            'errors': ['boom one', 'boom two'],
            'failure_details': [{'step': 'x'}],
            'metadata': {},
        }
        with patch('companies.infrastructure.workers.company_worker.create_initial_state'), \
             patch.object(worker, '_get_graph', return_value=MagicMock(invoke=MagicMock(return_value=result_dict))), \
             pytest.raises(RuntimeError, match='boom one | boom two'):
            worker._execute_pipeline(5, item)
        worker._pending_repo.update_fields.assert_called_once_with(
            5, "pending_companies", failure_reason=json.dumps([{'step': 'x'}], indent=2))

    def test_execute_pipeline_no_persistence_raises(self):
        from companies.infrastructure.workers.company_worker import CompanyWorker
        worker = _make_worker()
        item = {'notes': '[]', 'links': '[]', 'input_text': 'text'}
        result_dict = {
            'progress': {'completed_nodes': []},
            'errors': [],
            'failure_details': [],
            'metadata': {'persistence': {'success': False}},
        }
        with patch('companies.infrastructure.workers.company_worker.create_initial_state'), \
             patch.object(worker, '_get_graph', return_value=MagicMock(invoke=MagicMock(return_value=result_dict))), \
             pytest.raises(RuntimeError, match='failed to persist'):
            worker._execute_pipeline(5, item)

    def test_execute_pipeline_notes_as_list(self):
        from companies.infrastructure.workers.company_worker import CompanyWorker
        worker = _make_worker()
        item = {'notes': [{'type': 'text', 'content': 'list note'}], 'links': [], 'input_text': 'x'}
        result_dict = {
            'progress': {'completed_nodes': []},
            'errors': [],
            'failure_details': [],
            'metadata': {'persistence': {'success': True, 'company_id': 1, 'company_name': 'X'}},
        }
        with patch('companies.infrastructure.workers.company_worker.create_initial_state') as mock_init, \
             patch.object(worker, '_get_graph', return_value=MagicMock(invoke=MagicMock(return_value=result_dict))):
            result = worker._execute_pipeline(5, item)
        assert result == {'company_id': 1, 'name': 'X'}
        _, kwargs = mock_init.call_args
        assert 'list note' in kwargs['context']['notes']
