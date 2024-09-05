from __future__ import annotations

import logging
import subprocess as sp
from importlib import resources
from pathlib import Path
from shlex import split

import pandas as pd
import pytest


@pytest.fixture
def known_values() -> pd.DataFrame:
    known_csv = resources.path("ionfr.data.tests", "IonRM.csv")
    return pd.read_csv(known_csv)


@pytest.fixture
def run_cli() -> pd.DataFrame:
    ionex_file = resources.path("ionfr.data.tests", "codg2930.11i")
    # Need to escape spaces in the filename because of sys.argv
    ionex_file_str = ionex_file.as_posix().replace(" ", "\\ ")
    logging.info(ionex_file)
    cmd = f"ionFRM 08h37m05.6s+06d10m14.5s 52d54m54.6sn 6d52m11.7se 2011-10-20T00:00:00 {ionex_file_str}"
    logging.info(cmd)
    sp.run(split(cmd), check=True)

    output_file = Path.cwd() / "IonRM.csv"
    yield pd.read_csv(output_file)

    output_file.unlink()


def test_compute_rm(known_values, run_cli):
    pd.testing.assert_frame_equal(known_values, run_cli)
