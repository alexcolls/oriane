"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AwsModule = exports.SQS_SEARCH_ACCOUNTS_SERVICE = exports.SQS_INSTAGRAM_CONTENT_SERVICE = exports.SQS_INSTAGRAM_ACQUISITION_SERVICE = exports.SQS_INSTAGRAM_HANDLES_SERVICE = exports.SQS_SSCD_MODEL_SERVICE = exports.SQS_CONTENT_SERVICE = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const aws_sqs_service_1 = require("./aws.sqs.service");
const aws_s3_service_1 = require("./aws.s3.service");
const aws_os_service_1 = require("./aws.os.service");
const aws_cognito_service_1 = require("./aws.cognito.service");
exports.SQS_CONTENT_SERVICE = 'SQS_CONTENT_SERVICE';
exports.SQS_SSCD_MODEL_SERVICE = 'SQS_SSCD_MODEL_SERVICE';
exports.SQS_INSTAGRAM_HANDLES_SERVICE = 'SQS_INSTAGRAM_HANDLES_SERVICE';
exports.SQS_INSTAGRAM_ACQUISITION_SERVICE = 'SQS_INSTAGRAM_ACQUISITION_SERVICE';
exports.SQS_INSTAGRAM_CONTENT_SERVICE = 'SQS_INSTAGRAM_CONTENT_SERVICE';
exports.SQS_SEARCH_ACCOUNTS_SERVICE = 'SQS_SEARCH_ACCOUNTS_SERVICE';
const getSqsUrl = (configService, envVar) => {
    const queue = configService.get(envVar);
    if (!queue)
        throw new Error(`Missing ${envVar}`);
    const region = configService.get('AWS_REGION');
    if (!region)
        throw new Error('Missing AWS_REGION');
    const account = configService.get('AWS_ACCOUNT');
    if (!account)
        throw new Error('Missing AWS_ACCOUNT');
    const queueUrl = `https://sqs.${region}.amazonaws.com/${account}/${queue}`;
    return queueUrl;
};
let AwsModule = class AwsModule {
};
exports.AwsModule = AwsModule;
exports.AwsModule = AwsModule = __decorate([
    (0, common_1.Module)({
        imports: [config_1.ConfigModule],
        providers: [
            {
                provide: exports.SQS_CONTENT_SERVICE,
                useFactory: async (configService) => {
                    const queueUrl = getSqsUrl(configService, 'ORN_SQS_INSTAGRAM_ACQUISITION');
                    const service = new aws_sqs_service_1.AwsSqsService(configService, queueUrl);
                    await service.onModuleInit();
                    return service;
                },
                inject: [config_1.ConfigService],
            },
            {
                provide: exports.SQS_SSCD_MODEL_SERVICE,
                useFactory: async (configService) => {
                    const queueUrl = configService.get('AWS_SQS_SSCD_MODEL_URL');
                    if (!queueUrl)
                        throw new Error('Missing AWS_SQS_SSCD_MODEL_URL');
                    const service = new aws_sqs_service_1.AwsSqsService(configService, queueUrl);
                    await service.onModuleInit();
                    return service;
                },
                inject: [config_1.ConfigService],
            },
            {
                provide: exports.SQS_INSTAGRAM_HANDLES_SERVICE,
                useFactory: async (configService) => {
                    const queueUrl = getSqsUrl(configService, 'ORN_SQS_INSTAGRAM_HANDLES');
                    const service = new aws_sqs_service_1.AwsSqsService(configService, queueUrl);
                    await service.onModuleInit();
                    return service;
                },
                inject: [config_1.ConfigService],
            },
            {
                provide: exports.SQS_INSTAGRAM_ACQUISITION_SERVICE,
                useFactory: async (configService) => {
                    const queueUrl = getSqsUrl(configService, 'ORN_SQS_INSTAGRAM_ACQUISITION');
                    const service = new aws_sqs_service_1.AwsSqsService(configService, queueUrl);
                    await service.onModuleInit();
                    return service;
                },
                inject: [config_1.ConfigService],
            },
            {
                provide: exports.SQS_INSTAGRAM_CONTENT_SERVICE,
                useFactory: async (configService) => {
                    const queueUrl = getSqsUrl(configService, 'ORN_SQS_INSTAGRAM_CONTENT');
                    const service = new aws_sqs_service_1.AwsSqsService(configService, queueUrl);
                    await service.onModuleInit();
                    return service;
                },
                inject: [config_1.ConfigService],
            },
            {
                provide: exports.SQS_SEARCH_ACCOUNTS_SERVICE,
                useFactory: async (configService) => {
                    const queueUrl = getSqsUrl(configService, 'ORN_SQS_SEARCH_ACCOUNTS');
                    const service = new aws_sqs_service_1.AwsSqsService(configService, queueUrl);
                    await service.onModuleInit();
                    return service;
                },
                inject: [config_1.ConfigService],
            },
            aws_s3_service_1.AwsS3Service,
            aws_os_service_1.AwsOsService,
            aws_cognito_service_1.AwsCognitoService,
        ],
        exports: [
            exports.SQS_CONTENT_SERVICE,
            exports.SQS_SSCD_MODEL_SERVICE,
            exports.SQS_INSTAGRAM_ACQUISITION_SERVICE,
            exports.SQS_INSTAGRAM_CONTENT_SERVICE,
            exports.SQS_INSTAGRAM_HANDLES_SERVICE,
            exports.SQS_SEARCH_ACCOUNTS_SERVICE,
            aws_s3_service_1.AwsS3Service,
            aws_os_service_1.AwsOsService,
            aws_cognito_service_1.AwsCognitoService,
        ],
    })
], AwsModule);
//# sourceMappingURL=aws.module.js.map