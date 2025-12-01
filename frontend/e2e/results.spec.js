import { test, expect } from '@playwright/test';
import path from 'path';
import { collectCoverage } from './helpers/coverage';

test.describe('Results Page with Law Search', () => {
    test.beforeEach(async ({ page, context }) => {
        // Mock the backend /search endpoint
        await context.route('**/search', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([
                    {
                        filename: 'test_document',
                        originalFileName: 'test.txt',
                        references: ['LEGE_53_2003', 'HG_856_2020'],
                        law_details: {
                            'LEGE_53_2003': {
                                url: 'https://legislatie.just.ro/Public/DetaliiDocument/41500',
                                law: 'LEGE nr. 53 din 24 ianuarie 2003 - Codul muncii',
                                law_summary: 'Codul muncii reglementează relațiile de muncă',
                                relevant_article: 'Art. 5. Dreptul la muncă nu poate fi îngrădit',
                                articles_summary: 'Articolul garantează dreptul la muncă',
                                law_simplified: 'Legea stabilește regulile pentru contractele de muncă'
                            },
                            'HG_856_2020': {
                                url: 'https://legislatie.just.ro/Public/DetaliiDocument/229594',
                                law: 'HOTĂRÂRE nr. 856 din 2 septembrie 2020',
                                law_summary: 'Hotărârea stabilește măsuri',
                                relevant_article: 'Art. 1. Se aprobă',
                                articles_summary: 'Articolul aprobă măsurile',
                                law_simplified: 'Hotărârea aprobă măsuri pentru'
                            }
                        }
                    }
                ])
            });
        });

        await page.goto('http://localhost:3000');
        await page.waitForSelector('h1.text-5xl', { timeout: 50000 });
    });

    test.afterEach(async ({ page }) => {
        await collectCoverage(page);
    });

    test('should display results after file upload and confirmation', async ({ page }) => {
        // Upload file
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));

        // Wait for review modal
        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });

        // Confirm and proceed
        await page.locator('button:has-text("Confirm")').click();

        // Wait for results page
        await page.waitForURL('**/results', { timeout: 30000 });

        // Verify results are displayed
        await expect(page.locator('text=test.txt')).toBeVisible();
        await expect(page.locator('text=Referințe legale găsite')).toBeVisible();
    });

    test('should expand and display law details', async ({ page }) => {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));

        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });
        await page.locator('button:has-text("Confirm")').click();
        await page.waitForURL('**/results', { timeout: 30000 });

        // Expand file section
        await page.locator('text=test.txt').click();

        // Expand law details
        await page.locator('button:has-text("Lege 53")').first().click();

        // Verify law sections are visible
        await expect(page.locator('text=🔗 URL')).toBeVisible();
        await expect(page.locator('button:has-text("⚖️ Lege")')).toBeVisible();
        await expect(page.locator('button:has-text("📋 Sumar Lege")')).toBeVisible();
    });

    test('should display URL when expanded', async ({ page }) => {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));

        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });
        await page.locator('button:has-text("Confirm")').click();
        await page.waitForURL('**/results', { timeout: 30000 });

        // Expand file and law
        await page.locator('text=test.txt').click();
        await page.locator('button:has-text("Lege 53")').first().click();

        // Expand URL section
        await page.locator('button:has-text("🔗 URL")').click();

        // Verify URL is displayed
        await expect(page.locator('text=legislatie.just.ro')).toBeVisible();
    });

    test('should navigate back to home', async ({ page }) => {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));

        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });
        await page.locator('button:has-text("Confirm")').click();
        await page.waitForURL('**/results', { timeout: 30000 });

        // Click home button
        await page.locator('button:has-text("Home")').click();

        // Verify back at home
        await expect(page).toHaveURL('http://localhost:3000/');
        await expect(page.locator('h1.text-5xl')).toBeVisible();
    });

    test('should display extracted text preview', async ({ page }) => {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));

        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });
        await page.locator('button:has-text("Confirm")').click();
        await page.waitForURL('**/results', { timeout: 30000 });

        // Expand file
        await page.locator('text=test.txt').click();

        // Expand extracted text preview
        await page.locator('button:has-text("Extracted Text Preview")').click();

        // Verify extracted text is visible
        const extractedText = page.locator('pre');
        await expect(extractedText).toBeVisible();
    });
});
