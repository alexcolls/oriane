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
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
var AcquisitionController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AcquisitionController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const acquisition_service_1 = require("./acquisition.service");
let AcquisitionController = AcquisitionController_1 = class AcquisitionController {
    constructor(acquisitionService) {
        this.acquisitionService = acquisitionService;
        this.logger = new common_1.Logger(AcquisitionController_1.name);
    }
    async runAcquisition(batchSize) {
        this.logger.log('Received request to run main acquisition process.');
        const effectiveBatchSize = batchSize
            ? Math.min(Math.max(batchSize, 1), 10)
            : 10;
        return this.acquisitionService.runAcquisition(false, effectiveBatchSize);
    }
    async runAcquisitionDebug(batchSize) {
        this.logger.log('Received request to run main acquisition process (debug mode).');
        const effectiveBatchSize = batchSize
            ? Math.min(Math.max(batchSize, 1), 10)
            : 10;
        return this.acquisitionService.runAcquisition(true, effectiveBatchSize);
    }
    async runAcquisitionByUsername(username) {
        this.logger.log(`Received request to run acquisition for username: ${username}`);
        return await this.acquisitionService.runAcquisitionByUsername(username);
    }
    async runAcquisitionFast(batchSize) {
        this.logger.log('Received request to run FAST acquisition process.');
        const effectiveBatchSize = batchSize
            ? Math.min(Math.max(batchSize, 1), 10)
            : 10;
        return this.acquisitionService.runAcquisitionFast(false, effectiveBatchSize);
    }
    async runAcquisitionFastDebug(batchSize) {
        this.logger.log('Received request to run FAST acquisition process (debug mode).');
        const effectiveBatchSize = batchSize
            ? Math.min(Math.max(batchSize, 1), 10)
            : 10;
        return this.acquisitionService.runAcquisitionFast(true, effectiveBatchSize);
    }
    async runVideoContentUpdate(videoCode) {
        this.logger.log(`Received request to run video content update for code: ${videoCode}`);
        return await this.acquisitionService.runVideoContentUpdate(videoCode);
    }
    async getAcquisitionProgress() {
        this.logger.log('Received request to get acquisition progress.');
        return await this.acquisitionService.getAcquisitionProgress();
    }
    async getLastAcquisitionTimestamp() {
        this.logger.log('Received request for last acquisition timestamp.');
        return await this.acquisitionService.getLastAcquisitionTimestamp();
    }
    async getMessageFormat() {
        this.logger.log('Received request for SQS message format.');
        return this.acquisitionService.getMessageFormat();
    }
};
exports.AcquisitionController = AcquisitionController;
__decorate([
    (0, common_1.Post)('run-acquisition'),
    (0, swagger_1.ApiOperation)({
        summary: 'Trigger the main user acquisition process with batch processing',
    }),
    (0, swagger_1.ApiQuery)({
        name: 'batchSize',
        required: false,
        description: 'Number of messages per SQS batch (default: 10, max: 10 - AWS SQS limit)',
        type: Number,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Acquisition process finished, returns run statistics.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 500,
        description: 'Internal server error during acquisition.',
    }),
    __param(0, (0, common_1.Query)('batchSize')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Number]),
    __metadata("design:returntype", Promise)
], AcquisitionController.prototype, "runAcquisition", null);
__decorate([
    (0, common_1.Post)('run-acquisition-debug'),
    (0, swagger_1.ApiOperation)({
        summary: 'Trigger acquisition process with debug logging and batch processing',
    }),
    (0, swagger_1.ApiQuery)({
        name: 'batchSize',
        required: false,
        description: 'Number of messages per SQS batch (default: 10, max: 10 - AWS SQS limit)',
        type: Number,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Acquisition process finished with debug info.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 500,
        description: 'Internal server error during acquisition.',
    }),
    __param(0, (0, common_1.Query)('batchSize')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Number]),
    __metadata("design:returntype", Promise)
], AcquisitionController.prototype, "runAcquisitionDebug", null);
__decorate([
    (0, common_1.Post)('run-acquisition/:username'),
    (0, swagger_1.ApiOperation)({
        summary: 'Trigger acquisition process for a specific username',
    }),
    (0, swagger_1.ApiParam)({
        name: 'username',
        description: 'The username to process',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({ status: 200, description: 'Acquisition for user triggered.' }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'User not found.' }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __param(0, (0, common_1.Param)('username')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AcquisitionController.prototype, "runAcquisitionByUsername", null);
__decorate([
    (0, common_1.Post)('run-acquisition-fast'),
    (0, swagger_1.ApiOperation)({
        summary: 'Trigger ultra-fast acquisition process - loads all users in memory and sends in large batches',
        description: 'This endpoint is optimized for maximum speed by reducing database round trips. Use with caution for very large datasets as it loads all usernames into memory.',
    }),
    (0, swagger_1.ApiQuery)({
        name: 'batchSize',
        required: false,
        description: 'Number of messages per SQS batch (default: 10, max: 10 - AWS SQS limit)',
        type: Number,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Fast acquisition process finished, returns run statistics.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 500,
        description: 'Internal server error during fast acquisition.',
    }),
    __param(0, (0, common_1.Query)('batchSize')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Number]),
    __metadata("design:returntype", Promise)
], AcquisitionController.prototype, "runAcquisitionFast", null);
__decorate([
    (0, common_1.Post)('run-acquisition-fast-debug'),
    (0, swagger_1.ApiOperation)({
        summary: 'Trigger ultra-fast acquisition process with debug logging',
        description: 'This endpoint is optimized for maximum speed by reducing database round trips. Use with caution for very large datasets as it loads all usernames into memory.',
    }),
    (0, swagger_1.ApiQuery)({
        name: 'batchSize',
        required: false,
        description: 'Number of messages per SQS batch (default: 10, max: 10 - AWS SQS limit)',
        type: Number,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Fast acquisition process finished with debug info.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 500,
        description: 'Internal server error during fast acquisition.',
    }),
    __param(0, (0, common_1.Query)('batchSize')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Number]),
    __metadata("design:returntype", Promise)
], AcquisitionController.prototype, "runAcquisitionFastDebug", null);
__decorate([
    (0, common_1.Post)('run-acquisition/update-video/:videoCode'),
    (0, swagger_1.ApiOperation)({
        summary: 'Trigger video content update for a specific video code',
    }),
    (0, swagger_1.ApiParam)({
        name: 'videoCode',
        description: 'The video code to process for content update',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Video content update triggered successfully.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 500,
        description: 'Internal server error.',
    }),
    __param(0, (0, common_1.Param)('videoCode')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AcquisitionController.prototype, "runVideoContentUpdate", null);
__decorate([
    (0, common_1.Get)('progress'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get the current progress of the acquisition process',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Current acquisition progress statistics.',
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], AcquisitionController.prototype, "getAcquisitionProgress", null);
__decorate([
    (0, common_1.Get)('last-acquisition-timestamp'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get the timestamp of the last completed acquisition run',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Timestamp of the last acquisition or null.',
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], AcquisitionController.prototype, "getLastAcquisitionTimestamp", null);
__decorate([
    (0, common_1.Get)('message-format'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get the current SQS message format used by the acquisition service',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Message format documentation and example.',
    }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], AcquisitionController.prototype, "getMessageFormat", null);
exports.AcquisitionController = AcquisitionController = AcquisitionController_1 = __decorate([
    (0, swagger_1.ApiTags)('Acquisition'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('acquisition'),
    __metadata("design:paramtypes", [acquisition_service_1.AcquisitionService])
], AcquisitionController);
//# sourceMappingURL=acquisition.controller.js.map