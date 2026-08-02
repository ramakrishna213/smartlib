from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pytest

from appium_tests.utils.report_utils import write_excel_report

REPORT_PATH = Path(__file__).resolve().parent / "reports" / "pytest_appium_results.xlsx"
_RESULTS: List[Dict[str, object]] = []


def pytest_runtest_makereport(item, call):
    outcome = "passed"
    if call.excinfo is not None:
        outcome = "failed"
    elif call.when == "setup" and call.excinfo is not None:
        outcome = "failed"
    elif call.when == "call" and call.excinfo is None:
        outcome = "passed"

    if call.when == "call":
        _RESULTS.append(
            {
                "test_name": item.nodeid.split("::")[-1],
                "status": outcome,
                "duration": 0,
                "message": "",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        )

    return None


def pytest_sessionfinish(session, exitstatus):
    if _RESULTS:
        write_excel_report(_RESULTS, REPORT_PATH)
        print(f"\nAppium Excel report written to: {REPORT_PATH}")


@pytest.fixture(scope="module")
def appium_driver():
    return os.getenv("APPIUM_SERVER_URL", "http://127.0.0.1:4723/wd/hub")
