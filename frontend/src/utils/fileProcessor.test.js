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
            const text = 'Email: test@example.com, Phone: 0712 345 678, Another: admin@site.ro';
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
                const redacted = redactPII(t);
                expect(redacted).toBe(t);
            });
        });


    });
});
