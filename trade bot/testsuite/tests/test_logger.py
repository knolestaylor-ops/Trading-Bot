"""utils.logger.Logger, writing into a temporary directory."""
import logging
import uuid

import pytest

from utils.logger import Logger


@pytest.fixture
def make_logger(tmp_path):
    created = []

    def _make(name=None, **kwargs):
        logger = Logger(name=name or f"test-{uuid.uuid4().hex}", log_dir=tmp_path / "logs", **kwargs)
        created.append(logger)
        return logger

    yield _make

    for logger in created:
        for handler in list(logger.logger.handlers):
            handler.close()
            logger.logger.removeHandler(handler)


def log_text(tmp_path, logger):
    for handler in logger.logger.handlers:
        handler.flush()
    return (tmp_path / "logs" / f"{logger.logger.name}.log").read_text()


def test_creates_log_directory_and_file(tmp_path, make_logger):
    logger = make_logger()

    assert (tmp_path / "logs" / f"{logger.logger.name}.log").exists()


def test_writes_messages_with_level(tmp_path, make_logger):
    logger = make_logger()

    logger.info("order submitted")
    logger.warning("low buying power")
    logger.error("request failed")
    logger.critical("kill switch")

    text = log_text(tmp_path, logger)
    for level, message in [("INFO", "order submitted"), ("WARNING", "low buying power"),
                           ("ERROR", "request failed"), ("CRITICAL", "kill switch")]:
        assert f"{level} - {message}" in text


def test_debug_is_filtered_at_default_info_level(tmp_path, make_logger):
    logger = make_logger()

    logger.debug("noisy detail")

    assert "noisy detail" not in log_text(tmp_path, logger)


def test_debug_is_written_when_level_is_debug(tmp_path, make_logger):
    logger = make_logger(level=logging.DEBUG)

    logger.debug("noisy detail")

    assert "DEBUG - noisy detail" in log_text(tmp_path, logger)


def test_also_logs_to_console(make_logger, capsys):
    make_logger().error("visible")

    assert "visible" in capsys.readouterr().err


def test_same_name_does_not_duplicate_handlers(make_logger):
    name = f"test-{uuid.uuid4().hex}"
    first = make_logger(name=name)
    second = make_logger(name=name)

    assert first.logger is second.logger
    assert len(second.logger.handlers) == 2


def test_does_not_propagate_to_root_logger(make_logger):
    assert make_logger().logger.propagate is False


@pytest.mark.xfail(reason="the wrapper has no exception() method, so tracebacks can't be logged")
def test_can_log_exceptions_with_traceback(tmp_path, make_logger):
    logger = make_logger()
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        logger.exception("failed")

    assert "Traceback" in log_text(tmp_path, logger)
