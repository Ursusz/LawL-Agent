const webpack = require('webpack');

module.exports = function override(config, env) {
    // Polyfill Node.js core modules
    config.resolve.fallback = {
        ...config.resolve.fallback,
        "fs": false,
        "path": require.resolve("path-browserify"),
        "os": require.resolve("os-browserify/browser"),
        "crypto": require.resolve("crypto-browserify"),
        "stream": require.resolve("stream-browserify"),
        "buffer": require.resolve("buffer/"),
        "process": require.resolve("process/browser.js"),
        "url": require.resolve("url/"),
        "assert": require.resolve("assert/"),
        "util": require.resolve("util/"),
        "worker_threads": false,
        "module": require.resolve("./src/polyfills/module.js"),
    };

    // Patch scribe.js-ocr to force browser environment
    if (!config.module) {
        config.module = { rules: [] };
    }
    if (!config.module.rules) {
        config.module.rules = [];
    }

    // String replacement for scribe.js-ocr
    config.module.rules.unshift({
        test: /scribe\.js-ocr\/.*\.js$/,
        loader: require.resolve('string-replace-loader'),
        options: {
            multiple: [
                { search: "typeof process === 'object'", replace: 'false', flags: 'g' },
                { search: "typeof process === 'undefined'", replace: 'true', flags: 'g' },
                { search: "typeof process !== 'undefined'", replace: 'false', flags: 'g' }
            ]
        },
        enforce: 'pre'
    });

    // Handle WASM files as assets for wasm-pandoc
    config.module.rules.push({
        test: /\.wasm$/,
        type: 'asset/resource',
    });

    // Add plugins
    config.plugins = [
        ...config.plugins,
        new webpack.ProvidePlugin({
            Buffer: ['buffer', 'Buffer'],
        }),
        // Force typeof process to be 'undefined' for scribe.js-ocr compatibility
        new webpack.DefinePlugin({
            'typeof process': JSON.stringify('undefined'),
        }),
        // Handle node: protocol imports
        new webpack.NormalModuleReplacementPlugin(/^node:/, (resource) => {
            resource.request = resource.request.replace(/^node:/, "");
        }),
    ];

    // Exclude generalWorker from minification to avoid \"Unexpected token import\" errors
    if (config.optimization && config.optimization.minimizer) {
        config.optimization.minimizer.forEach(minimizer => {
            if (minimizer.constructor.name === 'TerserPlugin') {
                if (!minimizer.options.exclude) {
                    minimizer.options.exclude = [];
                }
                const oldExclude = minimizer.options.exclude;
                minimizer.options.exclude = oldExclude
                    ? (Array.isArray(oldExclude) ? [...oldExclude, /generalWorker/, /mupdf-worker/] : [oldExclude, /generalWorker/, /mupdf-worker/])
                    : [/generalWorker/, /mupdf-worker/];
            }
        });
    }

    // Ignore source map warnings for dependencies if needed
    config.ignoreWarnings = [/Failed to parse source map/];

    // Add babel-plugin-istanbul for coverage when REACT_APP_COVERAGE is true
    if (process.env.REACT_APP_COVERAGE === 'true') {
        // Find the babel loader
        const babelLoader = config.module.rules.find(
            rule => rule.oneOf
        )?.oneOf.find(
            rule => rule.loader && rule.loader.includes('babel-loader')
        );

        if (babelLoader) {
            if (!babelLoader.options.plugins) {
                babelLoader.options.plugins = [];
            }
            babelLoader.options.plugins.push('babel-plugin-istanbul');
        }
    }

    return config;
};
