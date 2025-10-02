"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AppModule = void 0;
const schedule_1 = require("@nestjs/schedule");
const config_1 = require("@nestjs/config");
const platform_express_1 = require("@nestjs/platform-express");
const bull_1 = require("@nestjs/bull");
const common_1 = require("@nestjs/common");
const serve_static_1 = require("@nestjs/serve-static");
const path_1 = require("path");
const multer_1 = require("multer");
const logger_middleware_1 = require("./middlewares/logger.middleware");
const database_module_1 = require("./database/database.module");
const auth_module_1 = require("./auth/auth.module");
const api_module_1 = require("./api/api.module");
let AppModule = class AppModule {
    configure(consumer) {
        consumer
            .apply(logger_middleware_1.LoggerMiddleware)
            .forRoutes({ path: 'handles/upload', method: common_1.RequestMethod.POST });
    }
};
exports.AppModule = AppModule;
exports.AppModule = AppModule = __decorate([
    (0, common_1.Module)({
        imports: [
            config_1.ConfigModule.forRoot({
                isGlobal: true,
            }),
            bull_1.BullModule.forRoot({
                redis: {
                    host: process.env.REDIS_HOST || 'localhost',
                    port: parseInt(process.env.REDIS_PORT || '6379'),
                },
            }),
            database_module_1.DatabaseModule,
            schedule_1.ScheduleModule.forRoot(),
            platform_express_1.MulterModule.register({
                storage: (0, multer_1.memoryStorage)(),
            }),
            serve_static_1.ServeStaticModule.forRoot({
                rootPath: (0, path_1.join)(__dirname, '..', 'public'),
            }),
            auth_module_1.AuthModule,
            api_module_1.ApiModule,
        ],
    })
], AppModule);
//# sourceMappingURL=app.module.js.map