"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.proxyInstagram = proxyInstagram;
const axios_1 = require("axios");
const main_1 = require("./main");
function proxyInstagram(app) {
    const expressApp = app.getHttpAdapter().getInstance();
    const proxyPath = `${main_1.BASE_PATH}/proxy`.replace(/\/{2,}/g, '/');
    expressApp.get(proxyPath, async (req, res) => {
        const url = decodeURIComponent(req.query.url);
        if (!url) {
            return res.status(400).send('No URL provided');
        }
        try {
            const response = await axios_1.default.get(url, {
                responseType: 'arraybuffer',
            });
            const contentType = response.headers['content-type'];
            if (!contentType) {
                throw new Error('Content-Type not found in response headers');
            }
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('Access-Control-Allow-Methods', 'GET, POST');
            res.setHeader('Content-Type', contentType);
            res.setHeader('Cache-Control', 'public, max-age=31536000');
            res.send(response.data);
        }
        catch (error) {
            console.error('Error fetching image:', error.message);
            res.status(500).send('Error fetching image');
        }
    });
}
//# sourceMappingURL=proxy.js.map