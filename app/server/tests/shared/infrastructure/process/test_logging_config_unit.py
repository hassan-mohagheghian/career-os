"""Tests for logging_config.py — setup_logging, get_logger."""
import sys, os, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
import shared.infrastructure.process.logging_config as lc


class TestSetupLogging:
    def _reset(self):
        lc._initialized = False

    def test_setup_with_log_dir(self, tmp_path):
        self._reset()
        lc.setup_logging(log_dir=str(tmp_path), level='DEBUG')
        import datetime
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        assert os.path.exists(os.path.join(str(tmp_path), f'pipeline_{today}.jsonl'))
        self._reset()

    def test_setup_without_log_dir(self):
        self._reset()
        lc.setup_logging(log_dir=None, level='INFO')
        assert lc._initialized is True
        self._reset()

    def test_setup_idempotent(self):
        self._reset()
        lc.setup_logging(level='INFO')
        assert lc._initialized is True
        lc.setup_logging(level='DEBUG')
        assert lc._initialized is True
        self._reset()

    def test_quiet_noisy_libraries(self):
        self._reset()
        lc.setup_logging(level='INFO')
        assert logging.getLogger('werkzeug').level == logging.WARNING
        assert logging.getLogger('engineio').level == logging.WARNING
        assert logging.getLogger('socketio').level == logging.WARNING
        self._reset()

    def test_root_logger_has_handlers(self):
        self._reset()
        lc.setup_logging(level='WARNING')
        root = logging.getLogger()
        assert len(root.handlers) > 0
        self._reset()

    def test_log_level_set(self):
        self._reset()
        lc.setup_logging(level='ERROR')
        root = logging.getLogger()
        assert root.level == logging.ERROR
        self._reset()

    def test_creates_log_dir(self, tmp_path):
        self._reset()
        nested = str(tmp_path / "logs" / "sub")
        lc.setup_logging(log_dir=nested, level='INFO')
        assert os.path.isdir(nested)
        self._reset()

    def test_setup_default_level(self):
        self._reset()
        lc.setup_logging()
        root = logging.getLogger()
        assert root.level == logging.INFO
        self._reset()


class TestGetLogger:
    def test_returns_bound_logger(self):
        log = lc.get_logger('test_module')
        assert hasattr(log, 'info')
        assert hasattr(log, 'error')

    def test_default_name(self):
        log = lc.get_logger()
        assert log is not None

    def test_logger_can_log(self):
        log = lc.get_logger('test_log')
        log.info("test_message", key="value")

    def test_different_names_return_loggers(self):
        log1 = lc.get_logger('module_a')
        log2 = lc.get_logger('module_b')
        assert log1 is not None
        assert log2 is not None
