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

    // Phone regex
    // Note: We need to be careful with the regex state if we reuse it, but here we define it fresh.
    // The previous regex was: /(?<!\/)(?:\+?\d[\d .-]{8,13}\d)/g
    const phoneRegex = /(?<!\/)(?:\+?\d[\d .-]{8,13}\d)/g;
    while ((match = phoneRegex.exec(text)) !== null) {
        matches.push({
            type: 'Phone',
            original: match[0],
            start: match.index,
            end: match.index + match[0].length,
            replacement: '[PHONE REDACTED]'
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
