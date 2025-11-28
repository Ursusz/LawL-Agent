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
            expect(redactedText).toBe('Contact me at [REDACTED] or [REDACTED]');
            expect(redactedItems).toHaveLength(2);
            expect(redactedItems[0]).toMatchObject({ type: 'Email', original: 'john.doe@example.com' });
            expect(redactedItems[0].start).toBe(14); // 'Contact me at '.length
            expect(redactedItems[1]).toMatchObject({ type: 'Email', original: 'jane@test.org' });
            expect(redactedItems[1].start).toBe(14 + 10 + 4); // 14 + '[REDACTED]'.length + ' or '.length
        });

        it('should redact phone numbers - Romanian format', () => {
            const text = 'My number is 0712 345 678 or 0723-456-789';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe('My number is [REDACTED] or [REDACTED]');
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
            expect(redactedText).toContain('[REDACTED]');
            expect(redactedText).not.toContain('test@example.com');
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
            expect(redactedText).toContain('[REDACTED]');
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

        it('should NOT redact dates as phone numbers', () => {
            const texts = [
                "Date: 28.02.2025",
                "Deadline: 31.12.2024",
                "Born on 15.03.1990",
                "ISO date: 2025-11-28",
                "Another date: 2024-01-15"
            ];
            texts.forEach(t => {
                const { redactedText, redactedItems } = redactPII(t);
                expect(redactedText).toBe(t);
                expect(redactedItems).toHaveLength(0);
            });
        });

        it('should NOT redact year ranges or reference numbers as phone numbers', () => {
            const texts = [
                "Reference: 2025-22801",
                "Case number: 2024-12345",
                "Document: 2023-98765"
            ];
            texts.forEach(t => {
                const { redactedText, redactedItems } = redactPII(t);
                expect(redactedText).toBe(t);
                expect(redactedItems).toHaveLength(0);
            });
        });

        it('should redact Romanian CNP', () => {
            const text = 'CNP: 1234567890123 and another CNP 9876543210987';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe('CNP: [REDACTED] and another CNP [REDACTED]');
            expect(redactedItems).toHaveLength(2);
            expect(redactedItems[0]).toMatchObject({ type: 'CNP', original: 'CNP: 1234567890123' });
            expect(redactedItems[1]).toMatchObject({ type: 'CNP', original: 'CNP 9876543210987' });
        });

        it('should redact Romanian last names (Nume)', () => {
            const text = 'Nume: Popescu and Nume de familie: Ionescu-Marin';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe('Nume: [REDACTED] and Nume de familie: [REDACTED]');
            expect(redactedItems).toHaveLength(2);
            expect(redactedItems[0]).toMatchObject({ type: 'Last Name', original: 'Nume: Popescu' });
            expect(redactedItems[1]).toMatchObject({ type: 'Last Name', original: 'Nume de familie: Ionescu-Marin' });
        });

        it('should redact Romanian first names (Prenume)', () => {
            const text = 'Prenume: Ion and Prenume: Maria-Elena';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe('Prenume: [REDACTED] and Prenume: [REDACTED]');
            expect(redactedItems).toHaveLength(2);
            expect(redactedItems[0]).toMatchObject({ type: 'First Name', original: 'Prenume: Ion' });
            expect(redactedItems[1]).toMatchObject({ type: 'First Name', original: 'Prenume: Maria-Elena' });
        });

        it('should handle Romanian characters in names', () => {
            const text = 'Nume: Ștefănescu, Prenume: Ștefan, Nume de familie: Țăran';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('[REDACTED]');
            expect(redactedItems).toHaveLength(3);
            expect(redactedItems[0].original).toBe('Nume: Ștefănescu');
            expect(redactedItems[1].original).toBe('Prenume: Ștefan');
            expect(redactedItems[2].original).toBe('Nume de familie: Țăran');
        });

        it('should redact all PII types in a complex Romanian document', () => {
            const text = `
                Nume de familie: Popescu
                Prenume: Ion
                CNP: 1234567890123
                Email: ion.popescu@example.com
                Telefon: 0712 345 678
            `;
            const { redactedText, redactedItems } = redactPII(text);

            expect(redactedItems.length).toBeGreaterThanOrEqual(5);
            expect(redactedItems.some(item => item.type === 'Last Name')).toBe(true);
            expect(redactedItems.some(item => item.type === 'First Name')).toBe(true);
            expect(redactedItems.some(item => item.type === 'CNP')).toBe(true);
            expect(redactedItems.some(item => item.type === 'Email')).toBe(true);
            expect(redactedItems.some(item => item.type === 'Phone')).toBe(true);

            // Check that all redactions are present
            expect(redactedText).toContain('[REDACTED]');
            // Phone with label uses [REDACTED] format
            expect(redactedText).toMatch(/Telefon:\s*\[REDACTED\]/);

            // Verify labels are preserved
            expect(redactedText).toContain('CNP:');
            expect(redactedText).toContain('Nume de familie:');
            expect(redactedText).toContain('Prenume:');
        });

        it('should NOT redact when only label words appear without actual name', () => {
            const text = 'Prenume și Nume sunt câmpuri obligatorii';
            const { redactedText } = redactPII(text);
            // Should not redact when there's no actual name following
            expect(redactedText).toBe(text);
        });

        it('should redact full names even after "Prenume și Nume" label', () => {
            const text = 'Prenume și Nume: Ion Popescu';
            const { redactedText, redactedItems } = redactPII(text);
            // "Ion Popescu" is a valid full name and should be redacted
            expect(redactedText).toBe('Prenume și Nume: [REDACTED]');
            // Could be classified as 'Name', 'First Name', 'Last Name', or 'Repeated Name'
            expect(redactedItems.length).toBeGreaterThan(0);
        });

        it('should redact "numele și prenumele" combined pattern', () => {
            const text = 'numele și prenumele: Popescu Ion';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe('numele și prenumele: [REDACTED]');
            expect(redactedItems).toHaveLength(1);
            expect(redactedItems[0].type).toBe('Name');
        });

        it('should redact "subsemnatul" pattern', () => {
            const text = 'subsemnatul Ion Popescu declar că';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe('subsemnatul [REDACTED] declar că');
            expect(redactedItems).toHaveLength(1);
            expect(redactedItems[0].type).toBe('Name');
        });

        it('should redact complex multi-part names', () => {
            const tests = [
                { input: 'Nume: Popescu-Ionescu', label: 'Nume:' },
                { input: 'Prenume: Maria-Elena', label: 'Prenume:' },
                { input: 'Prenume: Ion Vasile Constantin', label: 'Prenume:' },
                { input: 'Nume: De La Cruz', label: 'Nume:' },
                { input: 'subsemnatul Ion C. Popescu', label: 'subsemnatul' },
                { input: 'Subsemnatul Ion Popescu', label: 'Subsemnatul' },
                { input: 'subsemnata Ioana Ca-Popescu', label: 'subsemnata' },
                { input: 'Subsemnata Ana-Maria Popescu', label: 'Subsemnata' },
                { input: 'Prenume: Ab C. De', label: 'Prenume:' },
                { input: 'numele și prenumele: Popescu Ion Vasile', label: 'numele și prenumele:' }
            ];

            tests.forEach(({ input, label }) => {
                const { redactedText, redactedItems } = redactPII(input);
                expect(redactedText).toContain('[REDACTED]');
                expect(redactedText).toContain(label);
                expect(redactedItems.length).toBeGreaterThan(0);
            });
        });

        it('should redact identity card seria', () => {
            const text = 'seria: XX, nr: 123456';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('seria: [REDACTED]');
            expect(redactedItems.some(item => item.type === 'ID Seria')).toBe(true);
        });

        it('should redact identity card number', () => {
            const text = 'nr. 123456 eliberat de SPCLEP';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('nr. [REDACTED]');
            expect(redactedItems.some(item => item.type === 'ID Number')).toBe(true);
        });

        it('should redact issuing authority', () => {
            const text = 'eliberat de SPCLEP SECTOR 1';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('eliberat de [REDACTED]');
            expect(redactedItems.some(item => item.type === 'Issuing Authority')).toBe(true);
        });

        it('should redact birth date only in context', () => {
            const text = 'data nașterii: 28.02.1990';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('data nașterii: [REDACTED]');
            expect(redactedItems.some(item => item.type === 'Birth Date')).toBe(true);
        });

        it('should NOT redact dates without birth date context', () => {
            const text = 'Document emis la data: 28.02.2025';
            const { redactedText } = redactPII(text);
            expect(redactedText).toBe(text);
        });

        it('should handle OCR-spaced CNP', () => {
            const text = 'CNP: 1 2 3 4 5 6 7 8 9 0 1 2 3';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toBe('CNP: [REDACTED]');
            expect(redactedItems).toHaveLength(1);
            expect(redactedItems[0].type).toBe('CNP');
        });

        it('should handle OCR-spaced phone numbers', () => {
            const text = 'tel: 0 7 1 2 3 4 5 6 7 8';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('[REDACTED]');
            expect(redactedItems.some(item => item.type === 'Phone')).toBe(true);
        });

        it('should handle OCR-spaced birth dates', () => {
            const text = 'data nașterii: 2 8 . 0 2 . 1 9 9 0';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('data nașterii: [REDACTED]');
            expect(redactedItems.some(item => item.type === 'Birth Date')).toBe(true);
        });

        it('should redact phone with "tel" prefix', () => {
            const text = 'tel: 0712345678';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('[REDACTED]');
            expect(redactedItems.some(item => item.type === 'Phone')).toBe(true);
        });

        it('should redact phone with "tel." prefix', () => {
            const text = 'tel. 0712345678';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('[REDACTED]');
            expect(redactedItems.some(item => item.type === 'Phone')).toBe(true);
        });

        it('should redact phone with "tel. mobil" prefix', () => {
            const text = 'tel. mobil: 0712345678';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('[REDACTED]');
            expect(redactedItems.some(item => item.type === 'Phone')).toBe(true);
        });

        it('should detect and redact repeated names', () => {
            const text = `
                Nume: Popescu
                Mai jos, Popescu a declarat că...
            `;
            const { redactedText, redactedItems } = redactPII(text);

            // Should have both the original and the repeated redaction
            expect(redactedItems.some(item => item.type === 'Last Name')).toBe(true);
            expect(redactedItems.some(item => item.type === 'Repeated Name')).toBe(true);
            expect(redactedText).toContain('[REDACTED]');
        });

        it('should detect and redact repeated CNP', () => {
            const text = `
                CNP: 1234567890123
                Verificare: 1234567890123
            `;
            const { redactedText, redactedItems } = redactPII(text);

            expect(redactedItems.some(item => item.type === 'CNP')).toBe(true);
            expect(redactedItems.some(item => item.type === 'Repeated CNP')).toBe(true);
            expect(redactedText).toContain('[REDACTED]');
        });

        it('should handle complex identity document with all fields', () => {
            const text = `
                Numele și prenumele: Popescu Ion
                CNP: 1 2 3 4 5 6 7 8 9 0 1 2 3
                Seria: XX Nr: 123456
                Eliberat de: SPCLEP SECTOR 1
                Data nașterii: 28.02.1990
                Tel. mobil: 0712 345 678
                Email: ion.popescu@example.com
            `;
            const { redactedText, redactedItems } = redactPII(text);

            // Verify all types are detected
            expect(redactedItems.some(item => item.type === 'Name')).toBe(true);
            expect(redactedItems.some(item => item.type === 'CNP')).toBe(true);
            expect(redactedItems.some(item => item.type === 'ID Seria')).toBe(true);
            expect(redactedItems.some(item => item.type === 'ID Number')).toBe(true);
            expect(redactedItems.some(item => item.type === 'Issuing Authority')).toBe(true);
            expect(redactedItems.some(item => item.type === 'Birth Date')).toBe(true);
            expect(redactedItems.some(item => item.type === 'Phone')).toBe(true);
            expect(redactedItems.some(item => item.type === 'Email')).toBe(true);

            // Verify redactions are applied
            expect(redactedText).toContain('[REDACTED]');
            // Phone with label uses [REDACTED] format
            expect(redactedText).toMatch(/Tel\.?\s*mobil:\s*\[REDACTED\]/);
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

    describe('processManualEdit', () => {
        const { processManualEdit } = require('./fileProcessor');
        let originalDateNow;

        beforeAll(() => {
            originalDateNow = Date.now;
        });

        afterAll(() => {
            Date.now = originalDateNow;
        });

        it('should create a new edit when list is empty', () => {
            Date.now = jest.fn(() => 1000);
            const edits = [];
            const result = processManualEdit(edits, 'a', '', 0, 1, [], []);

            expect(result).toHaveLength(1);
            expect(result[0]).toMatchObject({
                type: 'Manual Edit',
                timestamp: 1000,
                position: 0,
                addedText: 'a',
                removedText: '',
                newText: 'a'
            });
        });

        it('should merge consecutive typing edits', () => {
            Date.now = jest.fn(() => 1000);
            const edits = [{
                type: 'Manual Edit',
                timestamp: 1000,
                position: 0,
                addedText: 'H',
                removedText: '',
                newText: 'H'
            }];

            Date.now = jest.fn(() => 1100); // 100ms later
            const result = processManualEdit(edits, 'He', 'H', 1, 1, [], []);

            expect(result).toHaveLength(1);
            expect(result[0].addedText).toBe('He');
            expect(result[0].newText).toBe('He');
            expect(result[0].timestamp).toBe(1100);
        });

        it('should merge even if time difference > 2s (no time limit)', () => {
            Date.now = jest.fn(() => 1000);
            const edits = [{
                type: 'Manual Edit',
                timestamp: 1000,
                position: 0,
                addedText: 'H',
                removedText: '',
                newText: 'H'
            }];

            Date.now = jest.fn(() => 3500); // 2.5s later
            const result = processManualEdit(edits, 'He', 'H', 1, 1, [], []);

            expect(result).toHaveLength(1);
            expect(result[0].addedText).toBe('He');
        });

        it('should merge backspace on recently added text', () => {
            Date.now = jest.fn(() => 1000);
            const edits = [{
                type: 'Manual Edit',
                timestamp: 1000,
                position: 0,
                addedText: 'Hi',
                removedText: '',
                newText: 'Hi'
            }];

            Date.now = jest.fn(() => 1100);
            // Backspace 'i' (pos 1, length 1)
            const result = processManualEdit(edits, 'H', 'Hi', 1, -1, [], []);

            expect(result).toHaveLength(1);
            expect(result[0].addedText).toBe('H');
            expect(result[0].newText).toBe('H');
        });

        it('should handle block undo (Ctrl+Z) as backspace', () => {
            Date.now = jest.fn(() => 1000);
            const edits = [{
                type: 'Manual Edit',
                timestamp: 1000,
                position: 0,
                addedText: 'Hello',
                removedText: '',
                newText: 'Hello'
            }];

            Date.now = jest.fn(() => 1100);
            // Undo "Hello" -> "" (pos 0, remove 5 chars)
            const result = processManualEdit(edits, '', 'Hello', 0, -5, [], []);

            expect(result).toHaveLength(0); // Should completely remove the edit
        });

        it('should remove edit if all added text is backspaced', () => {
            Date.now = jest.fn(() => 1000);
            const edits = [{
                type: 'Manual Edit',
                timestamp: 1000,
                position: 0,
                addedText: 'H',
                removedText: '',
                newText: 'H'
            }];

            Date.now = jest.fn(() => 1100);
            // Backspace 'H'
            const result = processManualEdit(edits, '', 'H', 0, -1, [], []);

            expect(result).toHaveLength(0);
        });

        it('should NOT merge if cursor moved (non-consecutive)', () => {
            Date.now = jest.fn(() => 1000);
            const edits = [{
                type: 'Manual Edit',
                timestamp: 1000,
                position: 0,
                addedText: 'A',
                removedText: '',
                newText: 'A'
            }];

            Date.now = jest.fn(() => 1100);
            // Insert 'B' at position 5 (not 1)
            const result = processManualEdit(edits, 'A    B', 'A    ', 5, 1, [], []);

            expect(result).toHaveLength(2);
        });

        it('should merge consecutive deletions (Backspace)', () => {
            Date.now = jest.fn(() => 1000);
            // Initial state: "Hello" -> "Hell" (deleted 'o')
            const edits = [{
                type: 'Manual Edit',
                timestamp: 1000,
                position: 4,
                addedText: '',
                removedText: 'o',
                originalText: 'Hello',
                newText: 'Hell'
            }];

            Date.now = jest.fn(() => 1100);
            // Backspace 'l' (pos 3)
            // oldText: "Hell", newText: "Hel"
            const result = processManualEdit(edits, 'Hel', 'Hell', 3, -1, [], []);

            expect(result).toHaveLength(1);
            expect(result[0].removedText).toBe('lo'); // 'l' + 'o'
            expect(result[0].position).toBe(3);
            expect(result[0].newText).toBe('Hel');
            expect(result[0].originalText).toBe('Hello');
        });

        it('should merge consecutive deletions (Delete key)', () => {
            Date.now = jest.fn(() => 1000);
            // Initial state: "Hello" -> "ello" (deleted 'H' at 0)
            const edits = [{
                type: 'Manual Edit',
                timestamp: 1000,
                position: 0,
                addedText: '',
                removedText: 'H',
                originalText: 'Hello',
                newText: 'ello'
            }];

            Date.now = jest.fn(() => 1100);
            // Delete 'e' (pos 0)
            // oldText: "ello", newText: "llo"
            const result = processManualEdit(edits, 'llo', 'ello', 0, -1, [], []);

            expect(result).toHaveLength(1);
            expect(result[0].removedText).toBe('He'); // 'H' + 'e'
            expect(result[0].position).toBe(0);
            expect(result[0].newText).toBe('llo');
            expect(result[0].originalText).toBe('Hello');
        });
    });

    describe('OCR spacing fixes', () => {
        it('should handle OCR-spaced seria (X X)', () => {
            const text = 'seria: X X, nr: 123456';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('seria: [REDACTED]');
            expect(redactedItems.some(item => item.type === 'ID Seria')).toBe(true);
            const seriaItem = redactedItems.find(item => item.type === 'ID Seria');
            expect(seriaItem.extractedValue).toBe('XX');
        });

        it('should handle eliberat de with extended text until "la data"', () => {
            const text = 'eliberat de SPCLEP SECTOR 1 BUCUREȘTI la data 28.02.2025';
            const { redactedText, redactedItems } = redactPII(text);
            expect(redactedText).toContain('eliberat de [REDACTED] la data');
            expect(redactedItems.some(item => item.type === 'Issuing Authority')).toBe(true);
        });

        it('should handle Romanian characters with both ș/ț and ş/ţ variants', () => {
            const texts = [
                'Nume: Ștefan',
                'Nume: Ştefan',
                'Prenume: Țăran',
                'Prenume: Ţăran'
            ];
            texts.forEach(text => {
                const { redactedText, redactedItems } = redactPII(text);
                expect(redactedText).toContain('[REDACTED]');
                expect(redactedItems.length).toBeGreaterThan(0);
            });
        });
    });
});
