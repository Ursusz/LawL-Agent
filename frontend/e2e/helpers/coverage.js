const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/**
 * Collects coverage from the page and saves it to .nyc_output
 * @param {import('@playwright/test').Page} page
 */
async function collectCoverage(page) {
    const coverage = await page.evaluate(() => window.__coverage__);
    if (coverage) {
        const coveragePath = path.join(
            __dirname,
            '../../.nyc_output',
            `coverage-${crypto.randomBytes(16).toString('hex')}.json`
        );

        // Ensure directory exists
        fs.mkdirSync(path.dirname(coveragePath), { recursive: true });

        fs.writeFileSync(coveragePath, JSON.stringify(coverage));
    }
}

module.exports = { collectCoverage };
