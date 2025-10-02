"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.retry = retry;
exports.cleanURL = cleanURL;
exports.sleep = sleep;
exports.downloadBufferFromUrl = downloadBufferFromUrl;
const axios_1 = require("axios");
async function retry(fn, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await fn();
        }
        catch (error) {
            if (attempt === maxRetries)
                throw error;
            await new Promise((resolve) => setTimeout(resolve, 1000 * attempt));
        }
    }
    throw new Error('Max retries reached');
}
function cleanURL(url) {
    return url.trim().replaceAll(/([^:]\/)\/+/g, '$1');
}
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
async function downloadBufferFromUrl(url) {
    const response = await axios_1.default.get(url, { responseType: 'arraybuffer' });
    return Buffer.from(response.data);
}
//# sourceMappingURL=index.js.map