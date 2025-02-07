const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    const htmlFile = process.argv[2]; // HTML file path
    const imgFile = process.argv[3];  // Output image file path

    if (!htmlFile || !imgFile) {
        console.error("Usage: node screenshot.js <htmlFile> <imgFile>");
        process.exit(1);
    }

    // Read HTML content
    const htmlContent = fs.readFileSync(htmlFile, 'utf8');

    // Launch Puppeteer
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();

    // Set content
    await page.setContent(htmlContent, { waitUntil: 'networkidle0' });

    // Capture screenshot
    await page.screenshot({ path: imgFile, fullPage: true });

    await browser.close();
})();
