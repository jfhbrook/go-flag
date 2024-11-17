# -*- coding: utf-8 -*-

import sys
from unittest.mock import Mock

import pytest

import flag.flag as flag
from flag.flag import ErrorHandling, FlagSet
from flag.flag import usage as usage_


@pytest.fixture
def default_usage():
    return usage_


@pytest.fixture
def command_line_usage():
    return usage_


@pytest.fixture
def usage(monkeypatch):
    usage = Mock()
    monkeypatch.setattr(flag, "usage", usage)
    return usage


@pytest.fixture
def output():
    mock = Mock(name="MockIO")
    return mock


def command_line(monkeypatch, command_line_usage, output) -> None:
    command_line = FlagSet(sys.argv[0], ErrorHandling.ContinueOnError)
    command_line.output = output
    command_line.usage = command_line_usage
    monkeypatch.setattr(flag, "command_line", command_line)
