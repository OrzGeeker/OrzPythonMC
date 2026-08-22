"""Shared pytest fixtures for library tests."""

from __future__ import annotations

import pytest
from fakes import FakeHttp, FakeReporter, FakeSink


@pytest.fixture
def reporter() -> FakeReporter:
    return FakeReporter()


@pytest.fixture
def sink() -> FakeSink:
    return FakeSink()


@pytest.fixture
def http() -> FakeHttp:
    return FakeHttp()
