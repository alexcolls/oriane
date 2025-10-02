"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LoggerMiddleware = void 0;
const common_1 = require("@nestjs/common");
let LoggerMiddleware = class LoggerMiddleware {
    constructor() {
        this.logger = new common_1.Logger('HTTP');
    }
    use(req, res, next) {
        const { method, originalUrl, ip } = req;
        const userAgent = req.get('user-agent') || '';
        this.logger.log(`Incoming Request: ${method} ${originalUrl} - IP: ${ip} - UserAgent: ${userAgent}`);
        if (process.env.NODE_ENV === 'development' &&
            Object.keys(req.body).length > 0) {
            this.logger.debug('Request Body:', JSON.stringify(req.body));
        }
        if (process.env.NODE_ENV === 'development' &&
            Object.keys(req.headers).length > 0) {
            this.logger.debug('Request Headers:', req.headers);
        }
        const now = Date.now();
        res.on('finish', () => {
            const { statusCode } = res;
            const contentLength = res.get('content-length');
            const duration = Date.now() - now;
            this.logger.log(`Response: ${method} ${originalUrl} ${statusCode} ${contentLength || '-'}b - ${duration}ms - IP: ${ip} - UserAgent: ${userAgent}`);
        });
        next();
    }
};
exports.LoggerMiddleware = LoggerMiddleware;
exports.LoggerMiddleware = LoggerMiddleware = __decorate([
    (0, common_1.Injectable)()
], LoggerMiddleware);
//# sourceMappingURL=logger.middleware.js.map