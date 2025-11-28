import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('File Upload and Processing', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3000');
        // Wait for the FileUpload component's title (the styled one)
        await page.waitForSelector('h1.text-5xl', { timeout: 50000 });
    });

    test('should upload and process a TXT file', async ({ page }) => {
        // Upload TXT file
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));

        // Wait for processing
        await page.waitForSelector('text=Processing...', { timeout: 20000 }).catch(() => { });

        // Wait for review modal to appear
        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });

        // Verify extracted text appears in textarea
        const textarea = page.locator('textarea');
        const extractedText = await textarea.inputValue();

        console.log('Extracted text:', extractedText);

        // Verify content is present
        expect(extractedText).toContain('plain text test file');

        // Verify PII is redacted
        expect(extractedText).toContain('[REDACTED]');
        expect(extractedText).not.toContain('user@domain.com');
        expect(extractedText).not.toContain('0723 456 789');
    });

    test('should upload and process a Markdown file', async ({ page }) => {
        // Upload MD file
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.md'));

        // Wait for review modal
        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });

        // Verify extracted text
        const textarea = page.locator('textarea');
        const extractedText = await textarea.inputValue();

        console.log('Extracted markdown:', extractedText);

        // Verify markdown content (headers should be preserved)
        expect(extractedText).toContain('# Sample Test Document');
        expect(extractedText).toContain('## Personal Information');

        // Verify PII is redacted  
        expect(extractedText).toContain('[REDACTED]');
        expect(extractedText).not.toContain('test.user@example.com');
        expect(extractedText).not.toContain('+40 712 345 678');
        expect(extractedText).not.toContain('admin@test.org');
    });

    test('should upload and process a PDF file', async ({ page }) => {
        // Upload PDF file from backend samples
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'backend_samples', 'sample.pdf'));

        // Wait for review modal (PDF might take longer)
        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 30000 });

        // Verify extracted text
        const textarea = page.locator('textarea');
        const extractedText = await textarea.inputValue();

        console.log('Extracted PDF text length:', extractedText.length);

        // Verify some content (assuming sample.pdf content)
        // Adjust expectation based on actual content if known, or just check length > 0
        expect(extractedText.length).toBeGreaterThan(0);
    });

    test('should upload and process a DOCX file', async ({ page }) => {
        // Upload DOCX file from backend samples
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'backend_samples', 'P5_UB_Declaratie.docx'));

        // Wait for review modal
        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 20000 });

        // Verify extracted text
        const textarea = page.locator('textarea');
        const extractedText = await textarea.inputValue();

        console.log('Extracted DOCX text length:', extractedText.length);
        expect(extractedText.length).toBeGreaterThan(0);
    });

    test('should upload and process an ODT file', async ({ page }) => {
        // Upload ODT file from backend samples
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'backend_samples', 'declaratie-pe-propria-raspundere-angajati.odt'));

        // Wait for review modal
        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 20000 });

        // Verify extracted text
        const textarea = page.locator('textarea');
        const extractedText = await textarea.inputValue();

        console.log('Extracted ODT text length:', extractedText.length);
        expect(extractedText.length).toBeGreaterThan(0);
    });

    test('should allow editing extracted text in review modal', async ({ page }) => {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));

        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });

        // Edit the text
        const textarea = page.locator('textarea');
        await textarea.fill('This is edited text');

        const editedText = await textarea.inputValue();
        expect(editedText).toBe('This is edited text');
    });

    test('should show original filename in review modal', async ({ page }) => {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));

        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });

        // Check filename is displayed
        await expect(page.locator('text=Original File: test.txt')).toBeVisible();
    });

    test('should cancel review and return to upload', async ({ page }) => {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.txt'));

        await expect(page.locator('text=Review Extracted Text')).toBeVisible({ timeout: 10000 });

        // Click cancel button
        await page.locator('button:has-text("Cancel")').first().click();

        // Should return to upload screen
        await expect(page.locator('text=Upload File')).toBeVisible();
        await expect(page.locator('text=Review Extracted Text')).not.toBeVisible();
    });

    test('should show error for unsupported file format', async ({ page }) => {
        // Create a file with unsupported extension
        const buffer = Buffer.from('test content');

        page.on('dialog', async dialog => {
            expect(dialog.message()).toContain('not supported');
            await dialog.accept();
        });

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles({
            name: 'test.xyz',
            mimeType: 'application/octet-stream',
            buffer: buffer
        });

        // Wait a bit for the error to appear
        await page.waitForTimeout(10000);
    });
});
