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
            const redacted = redactPII(text);
            expect(redacted).toBe('Contact me at [EMAIL REDACTED] or [EMAIL REDACTED]');
        });

        it('should redact phone numbers - international format', () => {
            const text = 'Call me at +40 123 456 789 or +1-234-567-8900';
            const redacted = redactPII(text);
            expect(redacted).toBe('Call me at [PHONE REDACTED] or [PHONE REDACTED]');
        });

        it('should redact phone numbers - Romanian format', () => {
            const text = 'My number is 0712 345 678 or 0723-456-789';
            const redacted = redactPII(text);
            expect(redacted).toBe('My number is [PHONE REDACTED] or [PHONE REDACTED]');
        });

        it('should handle empty text', () => {
            expect(redactPII('')).toBe('');
            expect(redactPII(null)).toBe('');
            expect(redactPII(undefined)).toBe('');
        });

        it('should redact multiple PII instances in one text', () => {
            const text = 'Email: test@example.com, Phone: +40 712 345 678, Another: admin@site.ro';
            const redacted = redactPII(text);
            expect(redacted).toContain('[EMAIL REDACTED]');
            expect(redacted).toContain('[PHONE REDACTED]');
            expect(redacted).not.toContain('test@example.com');
            expect(redacted).not.toContain('+40 712 345 678');
        });

        it('should preserve non-PII content', () => {
            const text = 'This is a normal sentence with numbers like 123 and words.';
            const redacted = redactPII(text);
            expect(redacted).toBe(text);
        });

        it('should handle complex email formats', () => {
            const text = 'Emails: first.last+tag@sub.domain.com, user_123@test.co.uk';
            const redacted = redactPII(text);
            expect(redacted).not.toContain('first.last+tag@sub.domain.com');
            expect(redacted).not.toContain('user_123@test.co.uk');
            expect(redacted).toContain('[EMAIL REDACTED]');
        });

        it('should handle phone with dots and dashes', () => {
            const text = 'Numbers: +1.234.567.8900, 0744-123-456, +40-123-456-789';
            const redacted = redactPII(text);
            expect(redacted).not.toContain('+1.234.567.8900');
            expect(redacted).not.toContain('0744-123-456');
            expect(redacted).toContain('[PHONE REDACTED]');
        });
    });
});
