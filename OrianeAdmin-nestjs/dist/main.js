"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BASE_PATH = exports.AWS_SQS_QUEUE_URL = exports.AWS_SECRET_ACCESS_KEY = exports.AWS_ACCESS_KEY_ID = exports.AWS_REGION = void 0;
const core_1 = require("@nestjs/core");
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const dotenv = require("dotenv");
const crypto = require("crypto");
const express = require("express");
const http_exception_filter_1 = require("./filters/http-exception.filter");
const roles_guard_1 = require("./guards/roles.guard");
const jwt_auth_guard_1 = require("./guards/jwt-auth.guard");
const app_module_1 = require("./app.module");
const proxy_1 = require("./proxy");
dotenv.config();
if (!globalThis.crypto) {
    globalThis.crypto = crypto.webcrypto;
}
exports.AWS_REGION = process.env.AWS_REGION || '';
exports.AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID || '';
exports.AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY || '';
exports.AWS_SQS_QUEUE_URL = process.env.AWS_SQS_QUEUE_URL || '';
exports.BASE_PATH = process.env.BASE_PATH || '/';
const CORS_FRONT = process.env.CORS_FRONT || 'http://localhost:5173';
const CORS_SWAGGER = process.env.CORS_SWAGGER || 'http://localhost:3000';
const CORS_MC = process.env.CORS_MC || 'https://manychat.com';
async function bootstrap() {
    const app = await core_1.NestFactory.create(app_module_1.AppModule);
    const logger = new common_1.Logger('Bootstrap');
    app.setGlobalPrefix(exports.BASE_PATH.replace(/\/$/, ''));
    const allowedOrigins = [
        CORS_FRONT.replace(/\/$/, ''),
        CORS_MC.replace(/\/$/, ''),
        CORS_SWAGGER.replace(/\/$/, ''),
    ];
    app.enableCors({
        origin: (origin, callback) => {
            if (!origin) {
                return callback(null, true);
            }
            if (allowedOrigins.includes(origin.replace(/\/$/, ''))) {
                callback(null, true);
            }
            else {
                logger.warn(`CORS policy blocked origin: ${origin}`);
                callback(new Error(`CORS policy does not allow origin: ${origin}`));
            }
        },
        methods: 'GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS',
        credentials: true,
        allowedHeaders: 'Content-Type, Authorization, X-Requested-With, Accept, Origin',
    });
    app.useGlobalPipes(new common_1.ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
        transformOptions: {
            enableImplicitConversion: true,
        },
    }));
    const reflector = app.get(core_1.Reflector);
    app.useGlobalGuards(new jwt_auth_guard_1.JwtAuthGuard(reflector), new roles_guard_1.RolesGuard(reflector));
    app.useGlobalFilters(new http_exception_filter_1.HttpExceptionFilter());
    app.use(express.json({ limit: '10mb' }));
    app.use(express.urlencoded({ extended: true, limit: '10mb' }));
    (0, proxy_1.proxyInstagram)(app);
    const swaggerConfig = new swagger_1.DocumentBuilder()
        .setTitle('Oriane Admin API')
        .setDescription('API documentation for the Oriane Admin API')
        .setVersion('0.1')
        .addBearerAuth()
        .build();
    const document = swagger_1.SwaggerModule.createDocument(app, swaggerConfig);
    swagger_1.SwaggerModule.setup(`${exports.BASE_PATH}/docs`, app, document);
    const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
    await app.listen(port, '0.0.0.0');
    logger.log(`Application is running on: http://localhost:${port}`);
}
bootstrap().catch((err) => {
    const logger = new common_1.Logger('BootstrapError');
    logger.error(`Failed to bootstrap application: ${err}`, err.stack);
    process.exit(1);
});
//# sourceMappingURL=main.js.map