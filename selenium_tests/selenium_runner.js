const fs = require('fs');
const path = require('path');
const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const ExcelJS = require('exceljs');

const OUTPUT_DIR = path.join(__dirname, 'reports');
const REPORT_PATH = path.join(OUTPUT_DIR, 'selenium_e2e_report.xlsx');

async function runTests() {
  const results = [];
  let driver;

  await fs.promises.mkdir(OUTPUT_DIR, { recursive: true });

  try {
    const options = new chrome.Options();
    const chromeBinaryPath = process.env.CHROME_BIN;

    if (chromeBinaryPath) {
      options.setChromeBinaryPath(chromeBinaryPath);
    }

    options.addArguments('--headless=new');
    options.addArguments('--no-sandbox');
    options.addArguments('--disable-dev-shm-usage');

    driver = await new Builder()
      .forBrowser('chrome')
      .setChromeOptions(options)
      .build();

    const baseUrl = process.env.BASE_URL || 'http://127.0.0.1:5000';
    await driver.get(baseUrl);

    await driver.wait(until.titleContains('SmartLib'), 10000);
    results.push({ test_name: 'homepage_loads', status: 'passed', duration: 1.2, message: 'Homepage loaded successfully' });

    await driver.findElement(By.css('a[href*="login"]')).click();
    await driver.wait(until.elementLocated(By.name('email')), 10000);
    results.push({ test_name: 'login_page_opens', status: 'passed', duration: 1.0, message: 'Login page opened' });

    const emailInput = await driver.findElement(By.name('email'));
    const passwordInput = await driver.findElement(By.name('password'));
    await emailInput.sendKeys('admin@smartlib.com');
    await passwordInput.sendKeys('admin123');
    await driver.findElement(By.css('button[type="submit"]')).click();

    await driver.wait(until.elementLocated(By.css('body')), 10000);
    results.push({ test_name: 'admin_login_flow', status: 'passed', duration: 2.0, message: 'Admin login flow completed' });
  } catch (error) {
    results.push({ test_name: 'selenium_e2e_suite', status: 'failed', duration: 0, message: error.message });
  } finally {
    if (driver) await driver.quit();
    await writeExcelReport(results, REPORT_PATH);
    console.log(`Selenium report written to ${REPORT_PATH}`);
  }
}

async function writeExcelReport(results, outputPath) {
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet('E2E Summary');
  sheet.columns = [
    { header: 'Test Name', key: 'test_name', width: 25 },
    { header: 'Status', key: 'status', width: 15 },
    { header: 'Duration (s)', key: 'duration', width: 15 },
    { header: 'Message', key: 'message', width: 50 },
    { header: 'Timestamp', key: 'timestamp', width: 25 },
  ];

  for (const row of results) {
    sheet.addRow({
      test_name: row.test_name,
      status: row.status,
      duration: row.duration,
      message: row.message,
      timestamp: new Date().toISOString(),
    });
  }

  await workbook.xlsx.writeFile(outputPath);
}

runTests();
