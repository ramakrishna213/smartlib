# Appium E2E Testing for SmartLib Android

This folder contains a separate Appium-based end-to-end test setup for the SmartLib Android application.

## What is included
- A pytest-based Appium suite for mobile E2E testing
- Excel report generation for each test run
- A dedicated reports folder for all outputs

## Setup
1. Install Python dependencies:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r appium_tests\requirements.txt
   ```
2. Install and start Appium Server.
3. Start an Android emulator or connect a real device.
4. Build the Android app and install it.

## Run the suite
```powershell
.\.venv\Scripts\python.exe -m pytest appium_tests/tests -q
```

## Generate an Excel report
```powershell
.\.venv\Scripts\python.exe appium_tests\run_appium_tests.py --demo
```

The report will be generated in:
- appium_tests/reports/appium_e2e_report.xlsx
