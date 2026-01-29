const { chromium } = require('playwright');

(async () => {
  console.log('Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Step 1: Navigate to the page
    console.log('Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { timeout: 60000, waitUntil: 'load' });

    // Step 2: Wait for page to fully load
    console.log('Waiting for page to load...');
    await page.waitForTimeout(3000);

    // Step 3: Take screenshot of initial state
    console.log('Taking screenshot of initial state...');
    await page.screenshot({
      path: '/Users/okis.chuang/Documents/dev/agent-will-smith/test-screenshots/01-initial-state.png',
      fullPage: true
    });
    console.log('Screenshot saved: 01-initial-state.png');

    // Step 4: Find and fill the text input
    console.log('Looking for text input...');
    
    // Find textarea
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      console.log('Found textarea, clicking to focus...');
      await textarea.click();
      await page.waitForTimeout(500);
      
      console.log('Typing message...');
      await textarea.fill('What CDN solution do you recommend for video streaming?');
      await page.waitForTimeout(500);

      // Take screenshot after typing
      await page.screenshot({
        path: '/Users/okis.chuang/Documents/dev/agent-will-smith/test-screenshots/02-after-typing.png',
        fullPage: true
      });
      console.log('Screenshot saved: 02-after-typing.png');

      // Find and click the send button (the orange arrow button)
      console.log('Looking for send button...');
      
      // Try finding the send button by aria-label or by finding the button with an SVG
      const sendButton = page.locator('button[aria-label*="Send"], button:has(svg[class*="lucide"])').last();
      
      if (await sendButton.isVisible()) {
        console.log('Found send button, clicking...');
        await sendButton.click();
      } else {
        // Try pressing Enter as fallback
        console.log('Send button not found, pressing Enter...');
        await textarea.press('Enter');
      }

      // Wait for response
      console.log('Waiting 10 seconds for response...');
      await page.waitForTimeout(10000);

      // Take screenshot of result
      console.log('Taking screenshot of result...');
      await page.screenshot({
        path: '/Users/okis.chuang/Documents/dev/agent-will-smith/test-screenshots/03-final-result.png',
        fullPage: true
      });
      console.log('Screenshot saved: 03-final-result.png');
    } else {
      console.log('Textarea not found!');
    }

    console.log('Test completed successfully!');

  } catch (error) {
    console.error('Error during test:', error.message);
    console.error(error.stack);

    try {
      await page.screenshot({
        path: '/Users/okis.chuang/Documents/dev/agent-will-smith/test-screenshots/error-state.png',
        fullPage: true
      });
      console.log('Error screenshot saved: error-state.png');
    } catch (e) {
      console.log('Could not take error screenshot');
    }
  } finally {
    await browser.close();
  }
})();
