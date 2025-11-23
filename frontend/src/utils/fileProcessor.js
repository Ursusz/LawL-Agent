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
    if (!text) return '';

    let redacted = text;

    // Redact email addresses
    redacted = redacted.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[EMAIL REDACTED]');

    // Redact phone numbers (10 or 11 digits, allowing common separators)
    // This regex matches optional leading + and country code, then a sequence of digits totaling 10 or 11 digits.
    // Allowed separators are spaces, dashes, periods, or parentheses. It deliberately excludes slashes to avoid redacting law numbers or dates.
    redacted = redacted.replace(/(?<!\/)(?:\+?\d[\d .-]{8,13}\d)/g, '[PHONE REDACTED]');

    return redacted;
};
