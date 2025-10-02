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
var OpenSearchController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.OpenSearchController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const aws_os_service_1 = require("../../aws/aws.os.service");
const opensearch_service_1 = require("./opensearch.service");
const opensearch_query_dto_1 = require("./dto/opensearch-query.dto");
let OpenSearchController = OpenSearchController_1 = class OpenSearchController {
    constructor(openSearchService, awsOsService) {
        this.openSearchService = openSearchService;
        this.awsOsService = awsOsService;
        this.logger = new common_1.Logger(OpenSearchController_1.name);
    }
    async searchVideosHybrid(queryDto) {
        this.logger.log(`Hybrid search request for query: "${queryDto.q}", size: ${queryDto.size}, num_candidates: ${queryDto.num_candidates}`);
        return this.openSearchService.searchVideosHybrid(queryDto.q, queryDto.size, queryDto.num_candidates);
    }
    async getFramesForVideo(videoOsId) {
        this.logger.log(`Request to get frames for videoOsId: ${videoOsId}`);
        const queryBody = { query: { term: { video_id: videoOsId } }, size: 10000 };
        return this.awsOsService.search('video_frames', queryBody);
    }
    async searchVideosByImageUrl(queryDto) {
        this.logger.log(`Visual search by URL request: ${queryDto.url}, k: ${queryDto.k}, numCandidates: ${queryDto.numCandidates}, platform: ${queryDto.platform}`);
        try {
            return this.openSearchService.searchVideosByImage(queryDto.url, queryDto.k, queryDto.numCandidates, queryDto.platform);
        }
        catch (e) {
            this.logger.error(`Error in searchVideosByImageUrl: ${e.message}`, e.stack);
            throw new common_1.HttpException(e.message || 'Error processing visual search by URL', e.status || common_1.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    async searchVideosByImageBase64(bodyDto, queryDto) {
        this.logger.log(`Visual search by Base64 image request, k: ${queryDto.k}, numCandidates: ${queryDto.numCandidates}, platform: ${queryDto.platform}`);
        try {
            return this.openSearchService.searchSimilarVideosFromBase64(bodyDto.b64, queryDto.k, queryDto.numCandidates, queryDto.platform);
        }
        catch (e) {
            this.logger.error(`Error in searchVideosByImageBase64: ${e.message}`, e.stack);
            throw new common_1.HttpException(e.message || 'Error processing visual search by Base64', e.status || common_1.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    async getEmbeddingForText(text) {
        this.logger.log(`Request to embed text: "${text.substring(0, 50)}..."`);
        return await this.openSearchService.embedText(text);
    }
};
exports.OpenSearchController = OpenSearchController;
__decorate([
    (0, common_1.Get)('search/videos/hybrid'),
    (0, swagger_1.ApiOperation)({
        summary: 'Perform a hybrid (text + vector) search for videos.',
    }),
    (0, swagger_1.ApiResponse)({ status: 200, description: 'Hybrid search results.' }),
    (0, swagger_1.ApiResponse)({
        status: 400,
        description: 'Bad request (e.g., missing query parameter).',
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [opensearch_query_dto_1.SearchVideosHybridQueryDto]),
    __metadata("design:returntype", Promise)
], OpenSearchController.prototype, "searchVideosHybrid", null);
__decorate([
    (0, common_1.Get)('frames/:videoOsId'),
    (0, swagger_1.ApiOperation)({
        summary: 'Retrieve all frame vectors for a specific video ID from OpenSearch.',
    }),
    (0, swagger_1.ApiParam)({
        name: 'videoOsId',
        description: 'The OpenSearch document ID for the video.',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({ status: 200, description: 'Frame vectors for the video.' }),
    (0, swagger_1.ApiResponse)({
        status: 404,
        description: 'Video ID not found in OpenSearch.',
    }),
    __param(0, (0, common_1.Param)('videoOsId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], OpenSearchController.prototype, "getFramesForVideo", null);
__decorate([
    (0, common_1.Get)('search/videos/by-image-url'),
    (0, swagger_1.ApiOperation)({
        summary: 'Perform a visual k-NN search for videos using an image URL.',
    }),
    (0, swagger_1.ApiResponse)({ status: 200, description: 'Visual search results.' }),
    (0, swagger_1.ApiResponse)({
        status: 400,
        description: 'Bad request (e.g., invalid URL or parameters).',
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [opensearch_query_dto_1.SearchVideosByUrlQueryDto]),
    __metadata("design:returntype", Promise)
], OpenSearchController.prototype, "searchVideosByImageUrl", null);
__decorate([
    (0, common_1.Post)('search/videos/by-image-base64'),
    (0, swagger_1.ApiOperation)({
        summary: 'Perform a visual k-NN search for videos using a Base64 encoded image.',
    }),
    (0, swagger_1.ApiResponse)({ status: 200, description: 'Visual search results.' }),
    (0, swagger_1.ApiResponse)({
        status: 400,
        description: 'Bad request (e.g., missing or invalid b64 data).',
    }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __param(1, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [opensearch_query_dto_1.SearchVideosByBase64BodyDto,
        opensearch_query_dto_1.SearchVideosByBase64QueryDto]),
    __metadata("design:returntype", Promise)
], OpenSearchController.prototype, "searchVideosByImageBase64", null);
__decorate([
    (0, common_1.Get)('utils/embed-text/:text'),
    (0, swagger_1.ApiOperation)({
        summary: 'Utility to get embedding for a given text string.',
    }),
    (0, swagger_1.ApiParam)({ name: 'text', description: 'Text to embed.', type: String }),
    (0, swagger_1.ApiResponse)({ status: 200, description: 'Text embedding vector.' }),
    __param(0, (0, common_1.Param)('text')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], OpenSearchController.prototype, "getEmbeddingForText", null);
exports.OpenSearchController = OpenSearchController = OpenSearchController_1 = __decorate([
    (0, swagger_1.ApiTags)('OpenSearch'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('opensearch'),
    __metadata("design:paramtypes", [opensearch_service_1.OpenSearchService,
        aws_os_service_1.AwsOsService])
], OpenSearchController);
//# sourceMappingURL=opensearch.controller.js.map