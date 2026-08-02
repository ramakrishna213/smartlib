# Selenium E2E Testing for SmartLib (Node.js)

This folder contains a separate Selenium-based end-to-end test setup for the SmartLib web application.

## What is included
- Selenium WebDriver tests for the web app
- Excel report generation using ExcelJS
- A dedicated reports folder for outputs

## Setup
1. Install Node.js dependencies:
   ```powershell
   cd selenium_tests
   npm install
   ```
2. Make sure the Flask web app is running:
   ```powershell
   .\.venv\Scripts\python.exe app.py
   ```
3. Run the tests:
   ```powershell
   npm test
   ```

The report will be generated at:
- selenium_tests/reports/selenium_e2e_report.xlsx
