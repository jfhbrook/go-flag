# -*- coding: utf-8 -*-

import sys
from typing import IO
from unittest.mock import Mock

import pytest

import flag.flag as flag
from flag.flag import ErrorHandling, FlagSet
from flag.flag import usage as usage_


@pytest.fixture
def default_usage():
    return usage_


@pytest.fixture
def usage(monkeypatch):
    usage = Mock()
    monkeypatch.setattr(flag, "usage", usage)
    return usage


@pytest.fixture
def output() -> IO:
    mock = Mock(name="MockIO")
    return mock


@pytest.fixture
def command_line(monkeypatch, usage, output) -> FlagSet:
    command_line = FlagSet(sys.argv[0], ErrorHandling.RAISE)
    command_line.output = output
    command_line.usage = usage
    monkeypatch.setattr(flag, "command_line", command_line)
    return command_line
