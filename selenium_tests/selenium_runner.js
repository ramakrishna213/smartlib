const fs = require('fs');
const path = require('path');
const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const ExcelJS = require('exceljs');

const OUTPUT_DIR = path.join(__dirname, 'reports', 'e2e');
const REPORT_PATH = path.join(OUTPUT_DIR, 'selenium_e2e_report.xlsx');
const JSON_REPORT_PATH = path.join(OUTPUT_DIR, 'selenium_e2e_report.json');

async function waitForApp(baseUrl) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < 20000) {
    try {
      const response = await fetch(baseUrl + '/');
      if (response.ok) {
        return;
      }
    } catch (error) {
      // Retry until the app is reachable.
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`App did not become reachable at ${baseUrl} within 20 seconds`);
}

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
    options.addArguments('--disable-gpu');
    options.addArguments('--window-size=1440,1200');

    driver = await new Builder()
      .forBrowser('chrome')
      .setChromeOptions(options)
      .build();

    await driver.manage().setTimeouts({ implicit: 10000 });

    const baseUrl = process.env.BASE_URL || 'http://127.0.0.1:5000';
    await waitForApp(baseUrl);

    await runStep(driver, results, 'homepage_loads', async () => {
      await driver.get(baseUrl + '/');
      await driver.wait(until.titleContains('SmartLib'), 10000);
      const title = await driver.getTitle();
      if (!title.includes('SmartLib')) {
        throw new Error(`Unexpected title: ${title}`);
      }
    });

    await runStep(driver, results, 'login_page_opens', async () => {
      await driver.get(baseUrl + '/login');
      await driver.wait(until.elementLocated(By.name('email')), 10000);
      const visible = await driver.findElement(By.name('email')).isDisplayed();
      if (!visible) {
        throw new Error('Login form is not visible');
      }
    });

    await runStep(driver, results, 'member_login_and_dashboard', async () => {
      await driver.findElement(By.name('email')).clear();
      await driver.findElement(By.name('email')).sendKeys('alex@example.com');
      await driver.findElement(By.name('password')).clear();
      await driver.findElement(By.name('password')).sendKeys('member123');
      await driver.findElement(By.css('button[type="submit"]')).click();
      await driver.wait(until.urlContains('/dashboard'), 10000);
      const heading = await driver.findElement(By.css('h1.page-title')).getText();
      if (!heading.includes('My Dashboard')) {
        throw new Error(`Unexpected dashboard heading: ${heading}`);
      }
    });

    await runStep(driver, results, 'logout_and_admin_login', async () => {
      await driver.get(baseUrl + '/logout');
      await driver.get(baseUrl + '/admin/login');
      await driver.wait(until.elementLocated(By.name('email')), 10000);

      const emailInput = await driver.findElement(By.name('email'));
      await emailInput.clear();
      await emailInput.sendKeys('admin@smartlib.com');

      const passwordInput = await driver.findElement(By.name('password'));
      await passwordInput.clear();
      await passwordInput.sendKeys('admin123');

      await driver.findElement(By.css('button[type="submit"]')).click();

      await driver.wait(async () => {
        try {
          const currentUrl = await driver.getCurrentUrl();
          const bodyText = await driver.findElement(By.tagName('body')).getText();
          return currentUrl.includes('/admin') || bodyText.includes('Admin Dashboard') || bodyText.includes('Welcome Admin') || bodyText.includes('Dashboard');
        } catch (error) {
          return false;
        }
      }, 15000);

      const bodyText = await driver.findElement(By.tagName('body')).getText();
      if (!bodyText.includes('Admin Dashboard') && !bodyText.includes('Welcome Admin') && !bodyText.includes('Dashboard')) {
        throw new Error(`Unexpected admin page content: ${bodyText.slice(0, 200)}`);
      }
    });

    await runStep(driver, results, 'books_catalog_access', async () => {
      await driver.get(baseUrl + '/books');
      await driver.wait(until.elementLocated(By.css('.book-title')), 10000);
      const bookTitles = await driver.findElements(By.css('.book-title'));
      if (bookTitles.length === 0) {
        throw new Error('No books were shown in catalog');
      }
    });

    await runStep(driver, results, 'member_registration_flow', async () => {
      const uniqueEmail = `selenium_${Date.now()}_${Math.random().toString(36).slice(2)}@example.com`;
      await driver.get(baseUrl + '/register');
      await driver.findElement(By.name('name')).sendKeys('Selenium Tester');
      await driver.findElement(By.name('email')).sendKeys(uniqueEmail);
      await driver.findElement(By.name('password')).sendKeys('Selenium123');
      await driver.findElement(By.name('student_id')).sendKeys(`STU-SEL-${Date.now()}`);
      await driver.findElement(By.name('department')).sendKeys('Engineering');
      await driver.findElement(By.css('button[type="submit"]')).click();

      await driver.wait(async () => {
        const currentUrl = await driver.getCurrentUrl();
        const bodyText = await driver.findElement(By.tagName('body')).getText();
        return currentUrl.includes('/login') || bodyText.includes('Create account') || bodyText.includes('Account created');
      }, 15000);

      const currentUrl = await driver.getCurrentUrl();
      const bodyText = await driver.findElement(By.tagName('body')).getText();
      if (!currentUrl.includes('/login') && !bodyText.includes('Create account') && !bodyText.includes('Account created')) {
        throw new Error(`Registration flow did not complete as expected. Current URL: ${currentUrl}`);
      }
    });
  } catch (error) {
    results.push({
      test_name: 'selenium_e2e_suite',
      status: 'failed',
      duration: 0,
      message: error.message,
    });
  } finally {
    if (driver) {
      await driver.quit();
    }

    await writeExcelReport(results, REPORT_PATH);
    await fs.promises.writeFile(JSON_REPORT_PATH, JSON.stringify({
      generated_at: new Date().toISOString(),
      total_tests: results.length,
      passed: results.filter((result) => result.status === 'passed').length,
      failed: results.filter((result) => result.status === 'failed').length,
      results,
    }, null, 2));

    const failedCount = results.filter((result) => result.status === 'failed').length;
    console.log(`Selenium E2E report written to ${REPORT_PATH}`);
    console.log(`Selenium E2E JSON summary written to ${JSON_REPORT_PATH}`);
    console.log(`Selenium E2E summary: ${results.length} total, ${failedCount} failed`);

    if (failedCount > 0) {
      process.exitCode = 1;
    }
  }
}

async function runStep(driver, results, testName, task) {
  const startedAt = Date.now();
  try {
    await task();
    results.push({
      test_name: testName,
      status: 'passed',
      duration: ((Date.now() - startedAt) / 1000).toFixed(2),
      message: 'Completed successfully',
    });
  } catch (error) {
    results.push({
      test_name: testName,
      status: 'failed',
      duration: ((Date.now() - startedAt) / 1000).toFixed(2),
      message: error.message,
    });
  }
}

async function writeExcelReport(results, outputPath) {
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet('E2E Summary');
  sheet.columns = [
    { header: 'Test Name', key: 'test_name', width: 28 },
    { header: 'Status', key: 'status', width: 15 },
    { header: 'Duration (s)', key: 'duration', width: 15 },
    { header: 'Message', key: 'message', width: 60 },
    { header: 'Timestamp', key: 'timestamp', width: 28 },
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
