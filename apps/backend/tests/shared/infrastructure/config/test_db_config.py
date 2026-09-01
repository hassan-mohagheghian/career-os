"""Tests for shared.infrastructure.config.db."""

import sys
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

import shared.infrastructure.config.db as db_module
from rules.infrastructure.models.rule_model import RuleModel


# ── _text_to_html (pure) ──────────────────────────────────────────

class TestTextToHtml:
    def test_all_caps_heading(self):
        html = db_module._text_to_html('SOFTWARE ENGINEER')
        assert '<h3' in html
        assert 'SOFTWARE ENGINEER' in html

    def test_named_headings(self):
        for heading in ('Summary', 'Experience', 'Education', 'Skills',
                        'Projects', 'Certifications', 'Languages'):
            html = db_module._text_to_html(heading)
            assert '<h3' in html

    def test_bullets(self):
        html = db_module._text_to_html('• point one\n- point two')
        assert html.count('<li') == 2
        assert 'point one' in html
        assert 'point two' in html

    def test_blank_lines(self):
        html = db_module._text_to_html('line one\n\nline two')
        assert html.count('<br/>') == 1

    def test_empty_text(self):
        assert db_module._text_to_html('') == '<br/>'

    def test_paragraph(self):
        html = db_module._text_to_html('plain line of text')
        assert '<p ' in html
        assert 'plain line of text' in html

    def test_whitespace_only_line(self):
        html = db_module._text_to_html('   \n  ')
        assert '<br/>' in html

    def test_all_caps_with_spaces_short(self):
        html = db_module._text_to_html('ABC')
        assert '<p ' in html


# ── load_json_to_db (no-op) ───────────────────────────────────────

class TestLoadJsonToDb:
    def test_noop(self):
        assert db_module.load_json_to_db() is None


# ── _seed_initial_rules ───────────────────────────────────────────

class TestSeedInitialRules:
    def test_seed(self, sa_session):
        db_module._seed_initial_rules(sa_session)
        assert sa_session.query(RuleModel).count() == 20

    def test_seed_rows_fields(self, sa_session):
        db_module._seed_initial_rules(sa_session)
        rule = sa_session.query(RuleModel).filter(RuleModel.key == 'python_backend_core').first()
        assert rule is not None
        assert rule.scope == 'JOB'
        assert rule.priority == 100


# ── init_db ───────────────────────────────────────────────────────

class TestInitDb:
    def test_init_db_seeds_rules(self, sa_session):
        fake_base = MagicMock()
        with patch('shared.infrastructure.database.sqlalchemy_config.ensure_schemas') as m_ensure, \
                patch('shared.infrastructure.database.sqlalchemy_config.engine', MagicMock()), \
                patch('shared.infrastructure.database.sqlalchemy_config.Base', fake_base), \
                patch('shared.infrastructure.database.sqlalchemy_config.SessionLocal', return_value=sa_session), \
                patch.object(db_module, '_seed_initial_rules') as m_seed:
            db_module.init_db()
        m_ensure.assert_called_once()
        fake_base.metadata.create_all.assert_called_once()
        m_seed.assert_called_once()

    def test_init_db_skips_seed_when_rules_exist(self, sa_session):
        sa_session.add(RuleModel(category='fit', scope='JOB', key='existing',
                                 value='x', priority=1, enabled=1, user_id='test-user'))
        sa_session.commit()
        fake_base = MagicMock()
        with patch('shared.infrastructure.database.sqlalchemy_config.ensure_schemas'), \
                patch('shared.infrastructure.database.sqlalchemy_config.engine', MagicMock()), \
                patch('shared.infrastructure.database.sqlalchemy_config.Base', fake_base), \
                patch('shared.infrastructure.database.sqlalchemy_config.SessionLocal', return_value=sa_session), \
                patch.object(db_module, '_seed_initial_rules') as m_seed:
            db_module.init_db()
        fake_base.metadata.create_all.assert_called_once()
        m_seed.assert_not_called()


# ── main block ────────────────────────────────────────────────────

def test_main_block():
    with open(db_module.__file__) as f:
        source = f.read()
    lines = source.splitlines(keepends=True)
    main_idx = next(
        i for i, l in enumerate(lines)
        if l.startswith('if __name__ == "__main__":')
    )
    head = "".join(lines[:main_idx])
    tail = "".join(lines[main_idx:])
    ns = {
        '__name__': '__main__',
        '__file__': db_module.__file__,
    }
    exec(compile(head, db_module.__file__, 'exec'), ns)
    ns['init_db'] = MagicMock()
    ns['load_json_to_db'] = MagicMock()
    ns['log'] = MagicMock()
    exec(compile(tail, db_module.__file__, 'exec'), ns)
    ns['init_db'].assert_called_once()
    ns['load_json_to_db'].assert_called_once()
