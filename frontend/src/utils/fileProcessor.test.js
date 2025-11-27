import { redactPII } from './fileProcessor';

// Mock the heavy dependencies
jest.mock('scribe.js-ocr', () => ({
    __esModule: true,
    default: {
        extractText: jest.fn()
    }
}));

jest.mock('mammoth', () => ({
    __esModule: true,
    default: {
        extractRawText: jest.fn()
    }
}));

jest.mock('wasm-pandoc', () => ({
    pandoc: jest.fn()
}));

describe('fileProcessor', () => {
    describe('redactPII', () => {
        it('should redact email addresses', () => {
            const text = 'Contact me at john.doe@example.com or jane@test.org';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe('Contact me at [EMAIL REDACTED] or [EMAIL REDACTED]');
            expect(redactedItems).toHaveLength(2);
            expect(redactedItems[0]).toMatchObject({ type: 'Email', original: 'john.doe@example.com' });
            expect(redactedItems[0].start).toBe(14); // 'Contact me at '.length
            expect(redactedItems[1]).toMatchObject({ type: 'Email', original: 'jane@test.org' });
            expect(redactedItems[1].start).toBe(14 + 16 + 4); // 14 + '[EMAIL REDACTED]'.length + ' or '.length
        });

        it('should redact phone numbers - Romanian format', () => {
            const text = 'My number is 0712 345 678 or 0723-456-789';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe('My number is [PHONE REDACTED] or [PHONE REDACTED]');
            expect(redactedItems).toHaveLength(2);
            expect(redactedItems[0]).toMatchObject({ type: 'Phone', original: '0712 345 678' });
            expect(redactedItems[1]).toMatchObject({ type: 'Phone', original: '0723-456-789' });
        });

        it('should handle empty text', () => {
            expect(redactPII('').redactedText).toBe('');
            expect(redactPII(null).redactedText).toBe('');
            expect(redactPII(undefined).redactedText).toBe('');
        });

        it('should redact multiple PII instances in one text', () => {
            const text = 'Email: test@example.com, Phone: 0712 345 678, Another: admin@site.ro';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('[EMAIL REDACTED]');
            expect(redactedText).toContain('[PHONE REDACTED]');
            expect(redactedItems).toHaveLength(3);

            // Verify order and indices
            expect(redactedItems[0].type).toBe('Email');
            expect(redactedItems[1].type).toBe('Phone');
            expect(redactedItems[2].type).toBe('Email');

            // Check that indices are increasing
            expect(redactedItems[1].start).toBeGreaterThan(redactedItems[0].end);
            expect(redactedItems[2].start).toBeGreaterThan(redactedItems[1].end);
        });

        it('should preserve non-PII content', () => {
            const text = 'This is a normal sentence with numbers like 123 and words.';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe(text);
            expect(redactedItems).toHaveLength(0);
        });

        it('should handle complex email formats', () => {
            const text = 'Emails: first.last+tag@sub.domain.com, user_123@test.co.uk';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).not.toContain('first.last+tag@sub.domain.com');
            expect(redactedText).not.toContain('user_123@test.co.uk');
            expect(redactedText).toContain('[EMAIL REDACTED]');
            expect(redactedItems).toHaveLength(2);
        });

        it('should not redact law references', () => {
            const texts = [
                "Legea nr. 53/2003",
                "Legea 287 din 2009",
                "HOTĂRÂRE DE GUVERN NR. 856 DIN 2020",
                "Ordonanta de urgenta nr. 195/2002",
                "Legea nr. 360/2023",
                "Hotărârea Guvernului nr. 100/2023",
                "OUG nr. 99 din 2006",
                "Ordin nr. 1855/2022",
                "Ordonanta nr. 30 din 2017",
                "LEGE nr. 31 din 16 noiembrie 1990 (*republicată*)",
                "Ordonanța de urgență nr. 119 din 24 octombrie 2022",
                "Hotărârea nr. 1000 din 27 decembrie 2023",
                "Ordinul nr. 1761/2006 al ministrului sănătății",
                "Decizia nr. 99/100/2020",
                "Ordinul nr. 483/184 din 10 iunie 1999",
                "Legea 188 din 1999",
                "OUG 117 din 2022",
                "OM nr. 4139/29.06.2022"
            ];
            texts.forEach(t => {
                const { redactedText } = redactPII(t);
                expect(redactedText).toBe(t);
            });
        });


    });

    describe('adjustRedactionPositions', () => {
        const { adjustRedactionPositions } = require('./fileProcessor');

        it('should shift positions forward when text is inserted before redaction', () => {
            const items = [
                { type: 'Email', original: 'test@example.com', start: 10, end: 26 }
            ];
            const result = adjustRedactionPositions(items, 5, 3); // Insert 3 chars at position 5
            expect(result[0].start).toBe(13);
            expect(result[0].end).toBe(29);
        });

        it('should not change positions when text is inserted after redaction', () => {
            const items = [
                { type: 'Email', original: 'test@example.com', start: 10, end: 26 }
            ];
            const result = adjustRedactionPositions(items, 30, 5); // Insert 5 chars at position 30
            expect(result[0].start).toBe(10);
            expect(result[0].end).toBe(26);
        });

        it('should expand redaction when text is inserted within it', () => {
            const items = [
                { type: 'Email', original: 'test@example.com', start: 10, end: 26 }
            ];
            const result = adjustRedactionPositions(items, 15, 3); // Insert 3 chars at position 15
            expect(result[0].start).toBe(10);
            expect(result[0].end).toBe(29); // End expands by 3
        });

        it('should shift positions backward when text is deleted before redaction', () => {
            const items = [
                { type: 'Email', original: 'test@example.com', start: 20, end: 36 }
            ];
            const result = adjustRedactionPositions(items, 5, -3); // Delete 3 chars at position 5
            expect(result[0].start).toBe(17);
            expect(result[0].end).toBe(33);
        });

        it('should remove redaction when it is completely deleted', () => {
            const items = [
                { type: 'Email', original: 'test@example.com', start: 10, end: 26 }
            ];
            const result = adjustRedactionPositions(items, 12, -20); // Delete 20 chars at position 12
            expect(result).toHaveLength(0); // Item should be removed
        });

        it('should handle multiple redactions with edit in middle', () => {
            const items = [
                { type: 'Email', original: 'first@example.com', start: 10, end: 27 },
                { type: 'Phone', original: '0712345678', start: 40, end: 50 },
                { type: 'Email', original: 'second@example.com', start: 60, end: 78 }
            ];
            const result = adjustRedactionPositions(items, 35, 5); // Insert 5 chars at position 35

            // First item should be unchanged (edit is after it)
            expect(result[0].start).toBe(10);
            expect(result[0].end).toBe(27);

            // Second and third items should shift forward
            expect(result[1].start).toBe(45);
            expect(result[1].end).toBe(55);
            expect(result[2].start).toBe(65);
            expect(result[2].end).toBe(83);
        });

        it('should return same items when offset is 0', () => {
            const items = [
                { type: 'Email', original: 'test@example.com', start: 10, end: 26 }
            ];
            const result = adjustRedactionPositions(items, 15, 0);
            expect(result).toEqual(items);
        });

        it('should handle empty items array', () => {
            const result = adjustRedactionPositions([], 10, 5);
            expect(result).toEqual([]);
        });

        it('should remove items with negative positions after deletion', () => {
            const items = [
                { type: 'Email', original: 'test@example.com', start: 5, end: 21 }
            ];
            const result = adjustRedactionPositions(items, 0, -10); // Delete 10 chars at start
            expect(result).toHaveLength(0); // Item should be removed (negative start)
        });
    });
});
