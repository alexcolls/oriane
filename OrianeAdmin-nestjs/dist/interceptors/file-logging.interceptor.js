"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var FileLoggingInterceptor_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.FileLoggingInterceptor = void 0;
const common_1 = require("@nestjs/common");
const operators_1 = require("rxjs/operators");
let FileLoggingInterceptor = FileLoggingInterceptor_1 = class FileLoggingInterceptor {
    constructor() {
        this.logger = new common_1.Logger(FileLoggingInterceptor_1.name);
    }
    intercept(context, next) {
        const request = context.switchToHttp().getRequest();
        if (request.file) {
            this.logger.log(`File received by Multer: Name: ${request.file.originalname}, Size: ${request.file.size}, MIME Type: ${request.file.mimetype}`);
        }
        else if (request.files) {
            this.logger.log(`Files received by Multer: Count: ${request.files.length}`);
            request.files.forEach((file) => {
                this.logger.log(`  File: Name: ${file.originalname}, Size: ${file.size}, MIME Type: ${file.mimetype}`);
            });
        }
        else {
            this.logger.debug('FileLoggingInterceptor: No file present on request at this stage (or no file uploaded).');
        }
        return next.handle().pipe((0, operators_1.tap)(() => {
            if (request.file) {
                this.logger.log(`File processing finished for: ${request.file.originalname}`);
            }
            else if (request.files) {
                this.logger.log(`Files processing finished for request to ${request.url}`);
            }
        }));
    }
};
exports.FileLoggingInterceptor = FileLoggingInterceptor;
exports.FileLoggingInterceptor = FileLoggingInterceptor = FileLoggingInterceptor_1 = __decorate([
    (0, common_1.Injectable)()
], FileLoggingInterceptor);
//# sourceMappingURL=file-logging.interceptor.js.map