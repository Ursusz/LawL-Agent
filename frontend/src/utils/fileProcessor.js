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

// Redact PII (Personally Identifiable Information)
export const redactPII = (text) => {
    if (!text) return { redactedText: '', redactedItems: [] };

    const matches = [];

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

    // Phone regex - improved to avoid false positives with dates and year ranges
    // Matches: +40 123 456 789, 0712-345-678, 0712.345.678, 0712 345 678, etc.
    // Avoids: 2025-22801, 28.02.2025, etc.
    // Pattern explanation:
    // - Must start with + or 0 (not just any digit)
    // - If starts with +, must be followed by 1-3 digits (country code)
    // - Then must have consistent separators (all spaces, all dashes, or all dots, or none)
    // - Total length should be appropriate for a phone number
    const phoneRegex = /(?<![\/\d])(?:\+\d{1,3}[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{2,4}|0\d{2,3}[\s.-]?\d{2,4}[\s.-]?\d{2,4}(?:[\s.-]?\d{2,4})?)(?![\d])/g;
    while ((match = phoneRegex.exec(text)) !== null) {
        // Additional validation: check that it's not a date-like pattern
        const matched = match[0];
        // Skip if it looks like a date (e.g., contains patterns like dd.mm.yyyy or yyyy-mm-dd)
        if (/^\d{1,2}[.\/]\d{1,2}[.\/]\d{2,4}$/.test(matched) || /^\d{4}[-\/]\d{1,2}[-\/]\d{1,2}$/.test(matched)) {
            continue;
        }
        // Skip if it's a year range or similar (e.g., 2025-22801)
        if (/^(19|20)\d{2}[-]\d+$/.test(matched)) {
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

    // Romanian CNP (Cod Numeric Personal) - 13 digits
    // Pattern: CNP followed by optional colon/space and 13 digits
    const cnpRegex = /\bCNP\s*:?\s*(\d{13})\b/gi;
    while ((match = cnpRegex.exec(text)) !== null) {
        matches.push({
            type: 'CNP',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(match[1], '[REDACTED]')
        });
    }

    // Romanian Last Name (Nume or Nume de familie)
    // Pattern: "Nume" or "Nume de familie" followed by optional colon/space and the actual name
    const lastNameRegex = /\b(?:Nume de familie|Nume)\s*:?\s*([A-ZĂÂÎȘȚ][a-zăâîșț]+(?:[-\s][A-ZĂÂÎȘȚ][a-zăâîșț]+)*)/g;
    while ((match = lastNameRegex.exec(text)) !== null) {
        matches.push({
            type: 'Last Name',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(match[1], '[REDACTED]')
        });
    }

    // Romanian First Name (Prenume)
    // Pattern: "Prenume" followed by optional colon/space and the actual name
    const firstNameRegex = /\bPrenume\s*:?\s*([A-ZĂÂÎȘȚ][a-zăâîșț]+(?:[-\s][A-ZĂÂÎȘȚ][a-zăâîșț]+)*)/g;
    while ((match = firstNameRegex.exec(text)) !== null) {
        matches.push({
            type: 'First Name',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: match[0].replace(match[1], '[REDACTED]')
        });
    }

    // Sort matches by start index
    matches.sort((a, b) => a.start - b.start);

    // Filter out overlapping matches (simple strategy: keep first, skip if overlaps with previous)
    const uniqueMatches = [];
    let lastEnd = 0;
    for (const m of matches) {
        if (m.start >= lastEnd) {
            uniqueMatches.push(m);
            lastEnd = m.end;
        }
    }

    // Reconstruct text and calculate new indices
    let redactedText = '';
    let currentIndex = 0;
    const redactedItems = [];

    for (const m of uniqueMatches) {
        // Append text before match
        redactedText += text.slice(currentIndex, m.start);

        // Calculate new start index in redacted text
        const newStart = redactedText.length;

        // Append replacement
        redactedText += m.replacement;

        // Calculate new end index
        const newEnd = redactedText.length;

        redactedItems.push({
            type: m.type,
            original: m.original,
            start: newStart,
            end: newEnd
        });

        currentIndex = m.end;
    }

    // Append remaining text
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
