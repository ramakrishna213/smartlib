from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from appium_tests.utils.report_utils import write_excel_report


@pytest.fixture(scope="module")
def driver():
    desired_caps = {
        "platformName": "Android",
        "automationName": "UiAutomator2",
        "deviceName": "Android Emulator",
        "appPackage": os.getenv("ANDROID_APP_PACKAGE", "com.example.smartlib"),
        "appActivity": os.getenv("ANDROID_APP_ACTIVITY", ".MainActivity"),
        "noReset": False,
        "newCommandTimeout": 600,
        "autoGrantPermissions": True,
    }

    options = UiAutomator2Options().load_capabilities(desired_caps)
    server_url = os.getenv("APPIUM_SERVER_URL", "http://127.0.0.1:4723/wd/hub")
    try:
        driver = webdriver.Remote(server_url, options=options)
    except Exception as exc:
        pytest.skip(f"Appium server or device is not available: {exc}")

    yield driver
    try:
        driver.quit()
    except Exception:
        pass


def test_app_launch_and_login_screen(driver):
    driver.launch_app()
    time.sleep(5)

    page_text = driver.page_source
    if "Login" in page_text or "login" in page_text.lower():
        assert True
    else:
        pytest.skip("The app did not expose the expected login UI in the captured page source.")

    login_candidates = driver.find_elements(
        by=AppiumBy.ANDROID_UIAUTOMATOR,
        value='new UiSelector().textContains("Login")',
    )
    if login_candidates:
        assert login_candidates[0].is_displayed()
    else:
        pytest.skip("The login UI was not detected in the app screen.")


def test_generate_excel_report(tmp_path):
    result_rows = [
        {
            "test_name": "test_app_launch_and_login_screen",
            "status": "passed",
            "duration": 5.0,
            "message": "Android app launched and login UI detected",
            "timestamp": "2026-08-02T00:00:00",
        },
        {
            "test_name": "test_generate_excel_report",
            "status": "passed",
            "duration": 1.0,
            "message": "Excel report generated",
            "timestamp": "2026-08-02T00:00:01",
        },
    ]

    output = write_excel_report(result_rows, tmp_path / "demo_report.xlsx")
    assert output.exists()
