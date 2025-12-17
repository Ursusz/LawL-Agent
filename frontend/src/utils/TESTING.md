# Testing Strategy for File Processor

## Unit Tests (fileProcessor.test.js)
- **Purpose**: Fast, isolated tests for PII redaction logic
- **Scope**: Tests `redactPII()` function with mocked dependencies
- **Why mocked**: Jest has issues with ES modules from scribe.js-ocr, mammoth, and wasm-pandoc
- **Coverage**: Email redaction, phone number redaction, edge cases

## Integration Tests (Needed)
For real file extraction testing with actual dependencies, we have two options:

### Option 1: Browser-based testing (Recommended)
Use Playwright or Cypress for end-to-end testing:
- Upload real PDF/DOCX/MD files
- Verify extraction works correctly
- Test review modal functionality
- Verify PII redaction in extracted text

### Option 2: Configure Jest for ES modules
Add to package.json:
```json
"jest": {
  "transformIgnorePatterns": [
    "node_modules/(?!(scribe.js-ocr|mammoth|wasm-pandoc)/)"
  ],
  "moduleNameMapper": {
    "\\.(wasm)$": "<rootDir>/__mocks__/fileMock.js"
  }
}
```

However, this is complex because:
- wasm-pandoc requires WASM binary loading
- scribe.js-ocr needs worker threads and WASM support
- These libraries are designed for browser environments, not Node.js/Jest

## Current Testing Approach
1. **Unit tests** verify PII redaction logic works correctly (✅ DONE)
2. **Manual testing** verifies file extraction with real files (✅ WORKING)
3. **Future**: Add Playwright E2E tests for full integration testing

## Running Tests
```bash
npm test -- fileProcessor.test.js          # Run unit tests
npm test -- --coverage                     # Check coverage
```
