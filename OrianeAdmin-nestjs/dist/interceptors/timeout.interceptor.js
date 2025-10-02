"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var TimeoutInterceptor_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.TimeoutInterceptor = void 0;
const common_1 = require("@nestjs/common");
const rxjs_1 = require("rxjs");
const operators_1 = require("rxjs/operators");
const config_1 = require("@nestjs/config");
let TimeoutInterceptor = TimeoutInterceptor_1 = class TimeoutInterceptor {
    constructor(configService) {
        this.configService = configService;
        this.logger = new common_1.Logger(TimeoutInterceptor_1.name);
        this.defaultTimeout = this.configService.get('HTTP_REQUEST_TIMEOUT_MS', 5000);
    }
    intercept(context, next) {
        const requestTimeout = this.defaultTimeout;
        return next.handle().pipe((0, operators_1.timeout)(requestTimeout), (0, operators_1.catchError)((err) => {
            if (err instanceof rxjs_1.TimeoutError) {
                const httpContext = context.switchToHttp();
                const request = httpContext.getRequest();
                this.logger.warn(`Request timeout after ${requestTimeout}ms for ${request.method} ${request.url}`);
                return (0, rxjs_1.throwError)(() => new common_1.RequestTimeoutException(`Request timed out after ${requestTimeout / 1000} seconds.`));
            }
            return (0, rxjs_1.throwError)(() => err);
        }));
    }
};
exports.TimeoutInterceptor = TimeoutInterceptor;
exports.TimeoutInterceptor = TimeoutInterceptor = TimeoutInterceptor_1 = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [config_1.ConfigService])
], TimeoutInterceptor);
//# sourceMappingURL=timeout.interceptor.js.map