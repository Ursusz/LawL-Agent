import { test, expect } from '@playwright/test';
import path from 'path';
import { collectCoverage } from './helpers/coverage';

test.describe('Results Page - Additional Coverage', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3000');
        await page.waitForSelector('h1.text-5xl', { timeout: 50000 });
    });

    test.afterEach(async ({ page }) => {
        await collectCoverage(page);
    });

    test('should handle law with ERROR field', async ({ page, context }) => {
        await context.route('**/search', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([{
                    filename: 'test',
                    originalFileName: 'test.txt',
                    references: ['LEGE_999_9999'],
                    law_details: {
                        'LEGE_999_9999': {
                            ERROR: 'Gemini did not return any answer.'
                        }
                    }
                }])
            });
        });

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));
        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });
        await page.locator('button:has-text("Confirm")').click();
        await page.waitForURL('**/results', { timeout: 30000 });

        await page.locator('text=test.txt').click();
        await page.locator('button:has-text("Lege 999")').first().click();

        // Verify error is displayed
        await expect(page.locator('text=EROARE GEMINI')).toBeVisible();
        await expect(page.locator('text=Gemini did not return any answer')).toBeVisible();
    });

    test('should handle empty law_details', async ({ page, context }) => {
        await context.route('**/search', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([{
                    filename: 'test',
                    originalFileName: 'test.txt',
                    references: [],
                    law_details: {}
                }])
            });
        });

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));
        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });
        await page.locator('button:has-text("Confirm")').click();
        await page.waitForURL('**/results', { timeout: 30000 });

        await page.locator('text=test.txt').click();

        // Verify message for no references
        await expect(page.locator('text=No references have been processed')).toBeVisible();
    });

    test('should copy all references for a file', async ({ page, context }) => {
        await context.route('**/search', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([{
                    filename: 'test',
                    originalFileName: 'test.txt',
                    references: ['LEGE_53_2003'],
                    law_details: {
                        'LEGE_53_2003': {
                            url: 'https://example.com',
                            law: 'Law text',
                            law_summary: 'Summary'
                        }
                    }
                }])
            });
        });

        // Grant clipboard permissions
        await context.grantPermissions(['clipboard-read', 'clipboard-write']);

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));
        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });
        await page.locator('button:has-text("Confirm")').click();
        await page.waitForURL('**/results', { timeout: 30000 });

        // Click copy all button (next to filename)
        const copyAllButton = page.locator('button:has-text("test.txt")').locator('..').locator('button').nth(1);
        await copyAllButton.click();

        // Wait for copy to complete (check icon changes)
        await page.waitForTimeout(500);
    });
});
