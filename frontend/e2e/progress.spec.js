import { test, expect } from '@playwright/test';

test('progress tracking displays correctly with mocked backend', async ({ page }) => {
    // Capture console logs
    page.on('console', msg => console.log(`[Browser] ${msg.text()} `));

    // Mock the search endpoint
    await page.route('http://localhost:8000/search', async route => {
        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 15000));
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify([
                {
                    filename: 'test.txt',
                    references: ['Legea 1/2000'],
                    law_details: {}
                }
            ])
        });
    });

    // Navigate to the app
    await page.goto('http://localhost:3000');

    // Inject MockEventSource
    await page.evaluate(() => {
        window.MockEventSource = class MockEventSource extends EventTarget {
            constructor(url) {
                super();
                this.url = url;
                this.readyState = 0; // CONNECTING
                console.log(`[MockEventSource] Constructed for ${url}`);

                setTimeout(() => {
                    this.readyState = 1; // OPEN
                    this.onopen && this.onopen({ type: 'open' });
                    console.log(`[MockEventSource] Opened`);
                    this.emitEvents();
                }, 100);
            }

            emitEvents() {
                const emit = (data) => {
                    const event = new MessageEvent('message', {
                        data: JSON.stringify(data),
                        origin: 'http://localhost:8000'
                    });
                    this.dispatchEvent(event);
                    this.onmessage && this.onmessage(event);
                    console.log(`[MockEventSource] Emitted event: ${data.type}`);
                };

                const events = [
                    { type: 'reference_extraction_start', data: { extraction_type: 'explicit' } },
                    { type: 'reference_extraction_complete', data: { extraction_type: 'explicit', references: ['Legea 1/2000'], count: 1 } },
                    { type: 'reference_extraction_start', data: { extraction_type: 'implicit' } },
                    { type: 'reference_extraction_complete', data: { extraction_type: 'implicit', references: ['Codul civil'], count: 1 } },
                    { type: 'reference_processing_start', data: { reference: 'Legea 1/2000' } },
                    { type: 'reference_stage_update', data: { reference: 'Legea 1/2000', stage: 'checking_cloud', cached: false } },
                    { type: 'reference_stage_update', data: { reference: 'Legea 1/2000', stage: 'checking_cache', cached: false } },
                    { type: 'reference_stage_update', data: { reference: 'Legea 1/2000', stage: 'generating_law_summary', cached: false } },
                    { type: 'reference_stage_update', data: { reference: 'Legea 1/2000', stage: 'generating_article_summary', cached: false } },
                    { type: 'reference_complete', data: { reference: 'Legea 1/2000', success: true } },
                    { type: 'reference_processing_start', data: { reference: 'Codul civil' } },
                    { type: 'reference_stage_update', data: { reference: 'Codul civil', stage: 'checking_cloud', cached: false } },
                    { type: 'reference_complete', data: { reference: 'Codul civil', success: true } },
                    { type: 'processing_complete', data: {} }
                ];

                let i = 0;
                const interval = setInterval(() => {
                    if (i >= events.length) {
                        clearInterval(interval);
                        this.close();
                        return;
                    }
                    emit({ ...events[i], timestamp: new Date().toISOString() });
                    i++;
                }, 1000);
            }

            close() {
                this.readyState = 2; // CLOSED
                console.log(`[MockEventSource] Closed`);
            }
        };

        window.EventSource = window.MockEventSource;
        console.log('[Test] Replaced window.EventSource');
    });

    // Create a dummy file for upload
    await page.setInputFiles('input[type="file"]', {
        name: 'test.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('This is a test file with Legea 1/2000.')
    });

    // Confirm upload (click the button in the review modal)
    // Wait for review modal to appear
    await expect(page.getByText('Review Extracted Text')).toBeVisible();

    // Click Confirm & Upload
    await page.getByRole('button', { name: 'Confirm & Upload' }).click();

    // Verify Loader appears
    await expect(page.getByText('Initializing...')).toBeVisible();

    // Wait for extraction to start
    await expect(page.getByText('Extracting explicit references...')).toBeVisible();

    // Verify "Extracting..." is replaced by "Found..." (not both visible)
    await expect(page.getByText('Found 1 explicit reference.')).toBeVisible();
    // The "Extracting explicit..." should no longer be the large text
    const extractingText = page.locator('p.text-xl').filter({ hasText: 'Extracting explicit' });
    await expect(extractingText).not.toBeVisible();

    // Verify the completion message is now the large text
    const foundText = page.getByText('Found 1 explicit reference.');
    await expect(foundText).toBeVisible();

    // Verify implicit references show in the UI
    await expect(page.getByText('Extracting implicit references...')).toBeVisible();
    await expect(page.getByText('Found 1 implicit reference.')).toBeVisible();

    // Verify implicit reference appears in the reference list
    await expect(page.getByText('Codul civil')).toBeVisible();

    // Verify implicit references section header appears
    await expect(page.getByText('Implicit References (1)')).toBeVisible();

    // Verify both explicit and implicit references show processing stages
    await expect(page.getByText('Processing Legea 1/2000...')).toBeVisible();
    await expect(page.getByText('Checking cloud storage')).toBeVisible();
    await expect(page.getByText('Checking cache')).toBeVisible();
    await expect(page.getByText('Generating')).toBeVisible();
    await expect(page.getByText('Completed Legea 1/2000.')).toBeVisible();
    await expect(page.getByText('Processing Codul civil...')).toBeVisible();

    // Verify reference cards show stages
    await expect(page.getByText('Checking cloud storage')).toBeVisible();
    // Verify completion messages replace processing messages
    await expect(page.getByText('Completed Codul civil.')).toBeVisible();

    // Verify final completion
    await expect(page.getByText('All processing complete!')).toBeVisible();

    // Verify the final message is large text
    const completeText = page.locator('p.text-xl').filter({ hasText: 'All processing complete' });
    await expect(completeText).toBeVisible();
});
