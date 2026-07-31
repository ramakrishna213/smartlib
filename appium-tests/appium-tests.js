const { remote } = require('webdriverio');

async function runAppiumFlow() {
  const caps = {
    platformName: 'Android',
    'appium:deviceName': 'Android Emulator',
    'appium:automationName': 'UiAutomator2',
    'appium:appPackage': 'com.example.app',
    'appium:appActivity': 'com.example.app.MainActivity',
    'appium:noReset': true
  };

  const driver = await remote({
    protocol: 'http',
    hostname: process.env.APPIUM_HOST || '127.0.0.1',
    port: 4723,
    path: '/wd/hub',
    capabilities: caps
  });

  try {
    await driver.pause(2000);
    console.log('Appium session started');
    return { status: 'passed', message: 'Appium session created' };
  } catch (error) {
    console.error('Appium test failed:', error.message);
    return { status: 'failed', message: error.message };
  } finally {
    await driver.deleteSession();
  }
}

(async () => {
  const result = await runAppiumFlow();
  console.log(JSON.stringify(result));
})();
