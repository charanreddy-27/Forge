"""Tests for structured JSON logging."""

import json
import logging

from forge.logsetup import JsonFormatter


def make_record(**kwargs) -> logging.LogRecord:
    defaults = dict(
        name="forge.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    defaults.update(kwargs)
    return logging.LogRecord(**defaults)


def test_formats_one_json_object_per_line():
    line = JsonFormatter().format(make_record())
    entry = json.loads(line)
    assert entry["level"] == "info"
    assert entry["logger"] == "forge.test"
    assert entry["message"] == "hello world"
    assert "ts" in entry
    assert "\n" not in line


def test_includes_exception_traceback():
    try:
        raise ValueError("kaboom")
    except ValueError:
        import sys

        record = make_record(
            level=logging.ERROR, msg="failed", args=(), exc_info=sys.exc_info()
        )
    entry = json.loads(JsonFormatter().format(record))
    assert "kaboom" in entry["exception"]
    assert "Traceback" in entry["exception"]
