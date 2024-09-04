from __future__ import annotations

import importlib.metadata

import ionfr as m


def test_version():
    assert importlib.metadata.version("ionfr") == m.__version__
