const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const REPORTS_DIR = path.resolve(__dirname, '../coverage');
const NYC_OUTPUT_DIR = path.resolve(__dirname, '../.nyc_output');
const JEST_COVERAGE_PATH = path.join(REPORTS_DIR, 'coverage-final.json');

// Ensure .nyc_output exists
if (!fs.existsSync(NYC_OUTPUT_DIR)) {
    fs.mkdirSync(NYC_OUTPUT_DIR, { recursive: true });
}

// Copy Jest coverage to .nyc_output if it exists
if (fs.existsSync(JEST_COVERAGE_PATH)) {
    console.log('Found Jest coverage, copying to .nyc_output...');
    fs.copyFileSync(
        JEST_COVERAGE_PATH,
        path.join(NYC_OUTPUT_DIR, 'jest-coverage.json')
    );
} else {
    console.log('No Jest coverage found at', JEST_COVERAGE_PATH);
}

// Run nyc merge and report
try {
    console.log('Merging coverage and generating reports...');
    // Use nyc to generate reports from .nyc_output
    execSync('npx nyc report --reporter=lcov --reporter=text --reporter=html', {
        stdio: 'inherit',
        cwd: path.resolve(__dirname, '..')
    });
    console.log('Coverage report generated in coverage/');
} catch (error) {
    console.error('Failed to generate coverage report:', error);
    process.exit(1);
}
