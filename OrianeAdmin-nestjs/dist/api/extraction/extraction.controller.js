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
var ExtractionController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtractionController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const aws_os_service_1 = require("../../aws/aws.os.service");
const extraction_service_1 = require("./extraction.service");
let ExtractionController = ExtractionController_1 = class ExtractionController {
    constructor(extractionService, awsOsService) {
        this.extractionService = extractionService;
        this.awsOsService = awsOsService;
        this.logger = new common_1.Logger(ExtractionController_1.name);
    }
    async extractAllVideos() {
        this.logger.log('Request received to run frame extraction for all eligible content.');
        return await this.extractionService.extractAllVideos();
    }
    async extractFramesByCode(code) {
        this.logger.log(`Request received to run frame extraction for code: ${code}`);
        return await this.extractionService.extractVideoByCode(code);
    }
    async getExtractionProgress() {
        this.logger.log('Request received to get extraction progress.');
        return await this.extractionService.getExtractionProgress();
    }
    async getLastExtractionTimestamp() {
        this.logger.log('Request received for last frame extraction timestamp.');
        return await this.extractionService.getLastExtractionTimestamp();
    }
    async verifyExtractionByCode(code) {
        this.logger.log(`Request received to verify frame extraction status for code: ${code}`);
        return await this.extractionService.verifyFramesExtractionByCode(code);
    }
    async verifyEmbeddingStatus(code) {
        this.logger.log(`Request received to verify embedding status for code: ${code}`);
        return this.extractionService.checkEmbeddingStatus(code);
    }
    async countVideos() {
        this.logger.log('Request received to count videos via AwsOsService.');
        const count = await this.awsOsService.count('videos');
        return { count };
    }
};
exports.ExtractionController = ExtractionController;
__decorate([
    (0, common_1.Post)('run/all'),
    (0, swagger_1.ApiOperation)({
        summary: 'Trigger cropping, scene detection, frame extraction, and embeddings for all eligible content.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Batch frame extraction process initiated. Returns statistics.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 500,
        description: 'Internal server error during the process.',
    }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], ExtractionController.prototype, "extractAllVideos", null);
__decorate([
    (0, common_1.Post)('run/:code'),
    (0, swagger_1.ApiOperation)({
        summary: 'Trigger cropping, scene detection, frame extraction, and embeddings for a single content item by its code.',
    }),
    (0, swagger_1.ApiParam)({
        name: 'code',
        description: 'The unique code of the content item.',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Frame extraction process for the code initiated or status returned.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 404,
        description: 'Content with the given code not found.',
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __param(0, (0, common_1.Param)('code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ExtractionController.prototype, "extractFramesByCode", null);
__decorate([
    (0, common_1.Get)('progress'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get overall content extraction progress (download, frames, embeddings).',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Current processing progress statistics.',
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], ExtractionController.prototype, "getExtractionProgress", null);
__decorate([
    (0, common_1.Get)('last-extraction-timestamp'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get the timestamp of the last completed frame extraction process.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Timestamp of the last extraction or null.',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], ExtractionController.prototype, "getLastExtractionTimestamp", null);
__decorate([
    (0, common_1.Get)('verify-frames/:code'),
    (0, swagger_1.ApiOperation)({
        summary: 'Verify if frames for a specific content item (by code) have been extracted.',
    }),
    (0, swagger_1.ApiParam)({
        name: 'code',
        description: 'The unique code of the content item.',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Returns true if extracted, false otherwise.',
        type: Boolean,
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __param(0, (0, common_1.Param)('code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ExtractionController.prototype, "verifyExtractionByCode", null);
__decorate([
    (0, common_1.Get)('verify-embeddings/:code'),
    (0, swagger_1.ApiOperation)({
        summary: 'Verify if a specific video (by code) has already been embedded.',
    }),
    (0, swagger_1.ApiParam)({
        name: 'code',
        description: 'The unique code of the video content.',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Returns embedding status.',
        schema: {
            example: { code: 'example_code', isEmbedded: true, exists: true },
        },
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __param(0, (0, common_1.Param)('code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ExtractionController.prototype, "verifyEmbeddingStatus", null);
__decorate([
    (0, common_1.Get)('verify-embeddings/count/videos'),
    (0, swagger_1.ApiOperation)({ summary: 'Get a count of videos from AwsOsService.' }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Count of videos.',
        schema: { example: { count: 123 } },
    }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], ExtractionController.prototype, "countVideos", null);
exports.ExtractionController = ExtractionController = ExtractionController_1 = __decorate([
    (0, swagger_1.ApiTags)('Extraction'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('extraction'),
    __metadata("design:paramtypes", [extraction_service_1.ExtractionService,
        aws_os_service_1.AwsOsService])
], ExtractionController);
//# sourceMappingURL=extraction.controller.js.map