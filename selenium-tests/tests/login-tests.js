const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

async function runLoginFlow(baseUrl) {
  const options = new chrome.Options();
  options.addArguments('--headless=new');
  options.addArguments('--no-sandbox');
  options.addArguments('--disable-dev-shm-usage');

  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .build();

  try {
    await driver.get(baseUrl + '/login');
    await driver.wait(until.elementLocated(By.name('email')), 10000);

    await driver.findElement(By.name('email')).sendKeys('alex@example.com');
    await driver.findElement(By.name('password')).sendKeys('member123');
    await driver.findElement(By.css('button[type="submit"]')).click();

    await driver.wait(until.urlContains('/dashboard'), 10000);
    const title = await driver.getTitle();
    console.log('Login test passed:', title);
    return { status: 'passed', message: 'Login flow completed successfully' };
  } catch (error) {
    console.error('Login test failed:', error.message);
    return { status: 'failed', message: error.message };
  } finally {
    await driver.quit();
  }
}

(async () => {
  const baseUrl = process.env.BASE_URL || 'http://127.0.0.1:5000';
  const result = await runLoginFlow(baseUrl);
  console.log(JSON.stringify(result));
})();
