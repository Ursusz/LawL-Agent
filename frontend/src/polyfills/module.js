export const createRequire = (url) => {
    return (specifier) => {
        console.warn(`[Polyfill] require('${specifier}') called from ${url}. Returning empty object.`);
        return {};
    };
};

export default {
    createRequire,
};
