import scribe from 'scribe.js-ocr';
import mammoth from 'mammoth';
import { pandoc } from 'wasm-pandoc';

// Helper: get file extension
const getExtension = (filename) => {
    return filename.split('.').pop().toLowerCase();
};

// Extract text from PDF using scribe.js-ocr
const extractOCR = async (file) => {
    const result = await scribe.extractText([file]);
    return result;
};

// Extract text from DOCX using mammoth
const extractDocx = async (file) => {
    const arrayBuffer = await file.arrayBuffer();
    const result = await mammoth.extractRawText({ arrayBuffer });
    return result.value;
};

// Simple markdown to text converter (fallback)
const convertMarkdown = (text) => {
    return text
        .replace(/^#{1,6}\s+/gm, '')
        .replace(/(\*\*|__)(.*?)\1/g, '$2')
        .replace(/(\*|_)(.*?)\1/g, '$2')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/!\[([^\]]*)\]\([^)]+\)/g, '')
        .replace(/```[\s\S]*?```/g, '')
        .replace(/`([^`]+)`/g, '$1')
        .trim();
};

// Extract using wasm-pandoc
const extractWithPandoc = async (file) => {
    try {
        const extension = getExtension(file.name);

        // Binary formats need to be passed as Blob, text formats as string
        const binaryFormats = ['odt', 'epub', 'docx', 'pdf', 'rtf', 'png', 'jpg', 'jpeg'];
        const isBinary = binaryFormats.includes(extension);

        const input = isBinary ? file : await file.text();

        // Map extensions to pandoc format names
        const formatMap = {
            'md': 'markdown',
            'markdown': 'markdown',
            'html': 'html',
            'htm': 'html',
            'rtf': 'rtf',
            'tex': 'latex',
            'latex': 'latex',
            'rst': 'rst',
            'org': 'org',
            'textile': 'textile',
            'mediawiki': 'mediawiki',
            'docbook': 'docbook',
            'epub': 'epub',
            'odt': 'odt',
        };

        const fromFormat = formatMap[extension] || 'markdown';

        console.log(`[fileProcessor] Converting ${extension} using pandoc: ${fromFormat} -> markdown`);

        const result = await pandoc(
            `-f ${fromFormat} -t markdown`,
            input,
            []
        );

        return result.out;
    } catch (error) {
        console.error('[fileProcessor] Pandoc conversion error:', error);
        // Fallback to simple markdown conversion if it's markdown, otherwise raw text
        const extension = getExtension(file.name);
        if (extension === 'md' || extension === 'markdown') {
            const text = await file.text();
            return convertMarkdown(text);
        }
        throw error;
    }
};

// Main extraction dispatcher
export const extractContent = async (file) => {
    const extension = getExtension(file.name);

    console.log(`[fileProcessor] Extracting ${extension} file:`, file.name);

    // Define supported formats
    const supportedFormats = [
        'pdf', 'png', 'jpeg', 'jpg', 'docx', 'txt',
        'md', 'markdown', 'html', 'htm', 'rtf', 'tex', 'latex',
        'rst', 'org', 'textile', 'mediawiki', 'docbook', 'epub', 'odt'
    ];

    if (!supportedFormats.includes(extension)) {
        throw new Error(
            `File format ".${extension}" is not supported.\n\n` +
            `Supported formats:\n` +
            `• PDF, DOCX, TXT\n` +
            `• Markdown (MD), HTML, RTF\n` +
            `• LaTeX (TEX), reStructuredText (RST)\n` +
            `• Org-mode (ORG), Textile, MediaWiki\n` +
            `• DocBook, EPUB, ODT\n\n` +
            `Please convert your file to one of these formats and try again.`
        );
    }

    try {
        if (extension === 'pdf' || extension === 'png' || extension === 'jpeg' || extension === 'jpg') {
            return await extractOCR(file);
        } else if (extension === 'docx') {
            return await extractDocx(file);
        } else if (extension === 'txt') {
            return await file.text();
        } else {
            // Use pandoc for all other supported formats
            return await extractWithPandoc(file);
        }
    } catch (error) {
        console.error('[fileProcessor] Extraction error:', error);
        throw new Error(
            `Failed to extract text from ${file.name}.\n\n` +
            `Error: ${error.message}\n\n` +
            `The file may be corrupted or in an unsupported variant of the format.`
        );
    }
};

// Helper function to normalize OCR-spaced text (e.g., "1 2 3 4" -> "1234")
const normalizeSpaces = (text) => {
    return text.replace(/\s+/g, '');
};

// Redact PII (Personally Identifiable Information)
export const redactPII = (text) => {
    if (!text) return { redactedText: '', redactedItems: [] };

    const matches = [];
    const extractedValues = {
        names: new Set(),
        cnp: new Set(),
        seria: new Set(),
        nr: new Set()
    };

    // Email regex
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
    let match;
    while ((match = emailRegex.exec(text)) !== null) {
        matches.push({
            type: 'Email',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: '[EMAIL REDACTED]'
        });
    }

    // Phone regex with variations (tel/tel./tel. mobil) and OCR spacing
    // Handles: tel: 0712 345 678, tel. mobil: 0 7 1 2 3 4 5 6 7 8, etc.
    const phoneWithLabelRegex = /\b((?:tel\.?\s*(?:mobil)?\s*:?\s*))(\+?\s*\d(?:\s*[\d\s.-]){8,15}\d)/gi;
    while ((match = phoneWithLabelRegex.exec(text)) !== null) {
        const label = match[1];
        const phoneNumber = match[2];
        const normalized = normalizeSpaces(phoneNumber);

        // Validate it's a reasonable phone number after normalization
        if (/^[\+\d][\d.-]{7,14}\d$/.test(normalized)) {
            matches.push({
                type: 'Phone',
                original: match[0],
                start: match.index,
                end: match.index + match[0].length,
                replacement: label + '[REDACTED]'
            });
        }
    }

    // Phone regex - improved to avoid false positives with dates and year ranges
    // Also handles OCR spacing: 0 7 1 2 3 4 5 6 7 8
    const phoneRegex = /(?<![\\/\d])(?:\+\s*\d{1,3}(?:\s*[\s.-]?\s*\d){7,12}|0\s*\d{2,3}(?:\s*[\s.-]?\s*\d){6,10})(?![\d])/g;
    while ((match = phoneRegex.exec(text)) !== null) {
        const matched = match[0];
        const normalized = normalizeSpaces(matched);

        // Skip if it looks like a date after normalization
        if (/^\d{1,2}[.\/]\d{1,2}[.\/]\d{2,4}$/.test(normalized) || /^\d{4}[-\/]\d{1,2}[-\/]\d{1,2}$/.test(normalized)) {
            continue;
        }
        // Skip if it's a year range
        if (/^(19|20)\d{2}[-]\d+$/.test(normalized)) {
            continue;
        }
        // Must be a valid phone length after normalization
        if (normalized.length < 9 || normalized.length > 15) {
            continue;
        }

        matches.push({
            type: 'Phone',
            original: matched,
            start: match.index,
            end: match.index + matched.length,
            replacement: '[PHONE REDACTED]'
        });
    }

    // Romanian CNP (Cod Numeric Personal) - 13 digits with optional OCR spacing
    // Handles: CNP: 1234567890123 or CNP: 1 2 3 4 5 6 7 8 9 0 1 2 3
    const cnpRegex = /\bCNP\s*:?\s*((?:\d\s*){12}\d)(?=\s|$|[^\d])/gi;
    while ((match = cnpRegex.exec(text)) !== null) {
        const cnpValue = match[1];
        const normalized = normalizeSpaces(cnpValue);

        // Verify it's exactly 13 digits after normalization
        if (/^\d{13}$/.test(normalized)) {
            extractedValues.cnp.add(normalized);
            matches.push({
                type: 'CNP',
                original: match[0],
                start: match.index,
                end: match.index + match[0].length,
                replacement: match[0].replace(cnpValue, '[REDACTED]'),
                extractedValue: normalized
            });
        }
    }

    // Identity Card Seria (2 uppercase letters)
    const seriaRegex = /\b(?:seria|ser\.?)\s*:?\s*([A-Z]{2})\b/gi;
    while ((match = seriaRegex.exec(text)) !== null) {
        extractedValues.seria.add(match[1]);
        matches.push({
            type: 'ID Seria',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(match[1], '[REDACTED]'),
            extractedValue: match[1]
        });
    }

    // Identity Card Nr (6-8 digits with optional OCR spacing)
    const nrRegex = /\b(?:nr\.?|număr)\s*(?:buletin|CI|carte\s+de\s+identitate)?\s*:?\s*((?:\d\s*){6,8})\b/gi;
    while ((match = nrRegex.exec(text)) !== null) {
        const nrValue = match[1];
        const normalized = normalizeSpaces(nrValue);

        if (/^\d{6,8}$/.test(normalized)) {
            extractedValues.nr.add(normalized);
            matches.push({
                type: 'ID Number',
                original: match[0],
                start: match.index,
                end: match.index + match[0].length,
                replacement: match[0].replace(nrValue, '[REDACTED]'),
                extractedValue: normalized
            });
        }
    }

    // Eliberat de (issuing authority)
    const eliberatRegex = /\b(?:eliberat(?:ă)?\s+de|emis(?:ă)?\s+de)\s*:?\s*([A-ZĂÂÎȘȚ][A-ZĂÂÎȘȚ\s\d.-]{3,50}?)(?=\s*(?:\n|$|,|;|\.|data))/gi;
    while ((match = eliberatRegex.exec(text)) !== null) {
        matches.push({
            type: 'Issuing Authority',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(match[1], '[REDACTED]')
        });
    }

    // Data nașterii (birth date) - only redact dates in this context
    // Handles OCR spacing: 2 8 . 0 2 . 1 9 9 0
    const birthDateRegex = /\b(?:data\s+nașterii|născut(?:ă)?\s+la)\s*:?\s*((?:\d\s*){1,2}\s*[.\/\s-]\s*(?:\d\s*){1,2}\s*[.\/\s-]\s*(?:\d\s*){2,4})/gi;
    while ((match = birthDateRegex.exec(text)) !== null) {
        matches.push({
            type: 'Birth Date',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(match[1], '[REDACTED]')
        });
    }

    // Context-aware name patterns
    // Handle inflections and avoid "prenume" followed by "nume" (and vice versa)

    // "Subsemnat" pattern (subsemnatul/subsemnata followed by name)
    // Handles: Ion Popescu, Maria-Elena Ionescu, Ion C. Popescu, etc.
    const subsemnatRegex = /\bsubsemnat(?:ul|a)\s+((?:[A-ZĂÂÎȘȚ][a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|[A-ZĂÂÎȘȚ]\.)(?:\s+(?:[A-ZĂÂÎȘȚ][a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|[A-ZĂÂÎȘȚ]\.))+)/g;
    while ((match = subsemnatRegex.exec(text)) !== null) {
        const name = match[1];
        extractedValues.names.add(name.toLowerCase());
        matches.push({
            type: 'Name',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(name, '[REDACTED]'),
            extractedValue: name
        });
    }

    // "Numele și prenumele" combined pattern
    // Handles complex names with multiple parts and initials
    const numelePrenumeleCombinedRegex = /\b(?:numele\s+și\s+prenumele|prenumele\s+și\s+numele)(?:\s+(?:din|de\s+pe)?\s*(?:actul\s+de\s+identitate|buletin|carte\s+de\s+identitate))?\s*:?\s*((?:[A-ZĂÂÎȘȚ][a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|[A-ZĂÂÎȘȚ]\.)(?:\s+(?:[A-ZĂÂÎȘȚ][a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|[A-ZĂÂÎȘȚ]\.))+)/gi;
    while ((match = numelePrenumeleCombinedRegex.exec(text)) !== null) {
        const name = match[1];
        extractedValues.names.add(name.toLowerCase());
        matches.push({
            type: 'Name',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(name, '[REDACTED]'),
            extractedValue: name
        });
    }

    // "Numele" (inflection) - but NOT if followed by "prenume" or "și prenume"
    // Handles: Popescu, Popescu-Ionescu, De La Cruz, etc.
    const numeleRegex = /\b(?:numele)(?!\s+(?:și\s+)?prenume\b)(?:\s+(?:din|de\s+pe)?\s*(?:actul\s+de\s+identitate|buletin|carte\s+de\s+identitate))?\s*:?\s*([A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.)(?:\s+[A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.))*)/gi;
    while ((match = numeleRegex.exec(text)) !== null) {
        const name = match[1];
        extractedValues.names.add(name.toLowerCase());
        matches.push({
            type: 'Last Name',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(name, '[REDACTED]'),
            extractedValue: name
        });
    }

    // "Prenumele" (inflection) - but NOT if followed by "nume" or "și nume"
    // Handles: Ion, Maria-Elena, Ion Vasile, etc.
    const prenumeleRegex = /\b(?:prenumele)(?!\s+(?:și\s+)?nume\b)(?:\s+(?:din|de\s+pe)?\s*(?:actul\s+de\s+identitate|buletin|carte\s+de\s+identitate))?\s*:?\s*([A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.)(?:\s+[A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.))*)/gi;
    while ((match = prenumeleRegex.exec(text)) !== null) {
        const name = match[1];
        extractedValues.names.add(name.toLowerCase());
        matches.push({
            type: 'First Name',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(name, '[REDACTED]'),
            extractedValue: name
        });
    }

    // "Nume de familie" - but NOT if followed by "și prenume" or just "prenume"
    // Handles: Popescu, Popescu-Ionescu, De La Cruz, etc.
    const numeDefamilieRegex = /\b(?:Nume\s+de\s+familie)(?!\s*:?\s*(?:și\s+)?[Pp]renume\b)\s*:?\s*([A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.)(?:\s+[A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.))*)/g;
    while ((match = numeDefamilieRegex.exec(text)) !== null) {
        const name = match[1];
        extractedValues.names.add(name.toLowerCase());
        matches.push({
            type: 'Last Name',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(name, '[REDACTED]'),
            extractedValue: name
        });
    }

    // "Nume" (simple) - but NOT if followed by "și Prenume" or just "Prenume"
    // Handles: Popescu, Popescu-Ionescu, De La Cruz, etc.
    const numeSimpleRegex = /\b(?:Nume)(?!\s+de\s+familie)(?!\s*:?\s*(?:și\s+)?[Pp]renume\b)\s*:?\s*([A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.)(?:\s+[A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.))*)/g;
    while ((match = numeSimpleRegex.exec(text)) !== null) {
        const name = match[1];
        extractedValues.names.add(name.toLowerCase());
        matches.push({
            type: 'Last Name',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(name, '[REDACTED]'),
            extractedValue: name
        });
    }

    // "Prenume" (simple) - but NOT if followed by "și Nume" or just "Nume"
    // Handles: Ion, Maria-Elena, Ion Vasile Constantin, Ion C., etc.
    const prenumeSimpleRegex = /\b(?:Prenume)(?!\s*:?\s*(?:și\s+)?[Nn]ume\b)\s*:?\s*([A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.)(?:\s+[A-ZĂÂÎȘȚ](?:[a-zăâîșț]+(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)*|\.))*)/g;
    while ((match = prenumeSimpleRegex.exec(text)) !== null) {
        const name = match[1];
        extractedValues.names.add(name.toLowerCase());
        matches.push({
            type: 'First Name',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(name, '[REDACTED]'),
            extractedValue: name
        });
    }

    // Sort matches by start index
    matches.sort((a, b) => a.start - b.start);

    // Before filtering overlaps, search for repeated occurrences of extracted values
    // Search for repeated names (case-insensitive) in original text
    for (const name of extractedValues.names) {
        if (name.length < 3) continue; // Skip very short names

        const nameRegex = new RegExp(`\\b${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
        let repeatMatch;

        while ((repeatMatch = nameRegex.exec(text)) !== null) {
            // Check if this overlaps with any existing match
            const overlaps = matches.some(m =>
                (repeatMatch.index >= m.start && repeatMatch.index < m.end) ||
                (m.start >= repeatMatch.index && m.start < repeatMatch.index + repeatMatch[0].length)
            );

            if (!overlaps) {
                matches.push({
                    type: 'Repeated Name',
                    original: repeatMatch[0],
                    start: repeatMatch.index,
                    end: repeatMatch.index + repeatMatch[0].length,
                    replacement: '[REPEATED NAME REDACTED]'
                });
            }
        }
    }

    // Search for repeated CNP (with optional OCR spacing) in original text
    for (const cnp of extractedValues.cnp) {
        const cnpWithSpaces = cnp.split('').join('\\s*');
        const cnpRegexRepeat = new RegExp(`\\b${cnpWithSpaces}\\b`, 'g');
        let repeatMatch;

        while ((repeatMatch = cnpRegexRepeat.exec(text)) !== null) {
            // Check if this overlaps with any existing match
            const overlaps = matches.some(m =>
                (repeatMatch.index >= m.start && repeatMatch.index < m.end) ||
                (m.start >= repeatMatch.index && m.start < repeatMatch.index + repeatMatch[0].length)
            );

            if (!overlaps) {
                matches.push({
                    type: 'Repeated CNP',
                    original: repeatMatch[0],
                    start: repeatMatch.index,
                    end: repeatMatch.index + repeatMatch[0].length,
                    replacement: '[REPEATED CNP REDACTED]'
                });
            }
        }
    }

    // Re-sort after adding repeated matches
    matches.sort((a, b) => a.start - b.start);

    // Filter out overlapping matches (keep first, skip if overlaps with previous)
    const uniqueMatches = [];
    let lastEnd = 0;
    for (const m of matches) {
        if (m.start >= lastEnd) {
            uniqueMatches.push(m);
            lastEnd = m.end;
        }
    }

    // Apply all redactions in one pass
    let redactedText = '';
    let currentIndex = 0;
    const redactedItems = [];

    for (const m of uniqueMatches) {
        redactedText += text.slice(currentIndex, m.start);
        const newStart = redactedText.length;
        redactedText += m.replacement;
        const newEnd = redactedText.length;

        redactedItems.push({
            type: m.type,
            original: m.original,
            start: newStart,
            end: newEnd
        });

        currentIndex = m.end;
    }
    redactedText += text.slice(currentIndex);

    return { redactedText, redactedItems };
};

// Adjust redaction positions after text edits
// editPosition: where the edit occurred in the text
// offset: positive for insertions, negative for deletions
// redactedItems: current array of redacted items
export const adjustRedactionPositions = (redactedItems, editPosition, offset) => {
    if (!redactedItems || redactedItems.length === 0 || offset === 0) {
        return redactedItems;
    }

    return redactedItems
        .map(item => {
            // If edit is completely after this redaction, no change needed
            if (editPosition >= item.end) {
                return item;
            }

            // If edit is completely before this redaction, shift both start and end
            if (editPosition <= item.start) {
                const newStart = item.start + offset;
                const newEnd = item.end + offset;

                // If deletion causes negative positions, mark as invalid
                if (newStart < 0 || newEnd < 0) {
                    return null;
                }

                return {
                    ...item,
                    start: newStart,
                    end: newEnd
                };
            }

            // Edit is within the redaction - adjust only the end
            if (editPosition > item.start && editPosition < item.end) {
                const newEnd = item.end + offset;

                // If deletion causes end to be before start, mark as invalid
                if (newEnd <= item.start) {
                    return null;
                }

                return {
                    ...item,
                    end: newEnd
                };
            }

            return item;
        })
        .filter(item => item !== null); // Remove invalid items
};
