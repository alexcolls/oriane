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
Object.defineProperty(exports, "__esModule", { value: true });
exports.AiResultsController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const ai_results_service_1 = require("./ai-results.service");
const ai_results_entity_1 = require("../../../entities/ai-results.entity");
const ai_results_dto_1 = require("./dto/ai-results.dto");
let AiResultsController = class AiResultsController {
    constructor(aiResultsService) {
        this.aiResultsService = aiResultsService;
    }
    async getAiResults(queryDto) {
        const { offset, limit, order, sortBy, search } = queryDto;
        return await this.aiResultsService.getAiResults(offset, limit, order, sortBy, search);
    }
    async getAiMatches(queryDto) {
        const { offset, limit, order, sortBy, search } = queryDto;
        return this.aiResultsService.getAiMatches(offset, limit, order, sortBy, search);
    }
    async getAiMatchesCountByJobId(jobId, queryDto) {
        return this.aiResultsService.getAiMatchesCountByJobId(jobId, queryDto.threshold ?? 0.5);
    }
    async getAiResultById(id) {
        return this.aiResultsService.getAiResultById(id);
    }
    async createAiResult(createAiResultDto) {
        return this.aiResultsService.createAiResult(createAiResultDto);
    }
    async updateAiResult(id, updateAiResultDto) {
        return this.aiResultsService.updateAiResult(id, updateAiResultDto);
    }
    async deleteAiResult(id) {
        await this.aiResultsService.deleteAiResult(id);
    }
};
exports.AiResultsController = AiResultsController;
__decorate([
    (0, common_1.Get)('all'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get all AI results with pagination, sorting, and search',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Paginated list of AI results.',
        type: ai_results_dto_1.PaginatedAiResultsResponseDto,
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_results_dto_1.GetAiResultsQueryDto]),
    __metadata("design:returntype", Promise)
], AiResultsController.prototype, "getAiResults", null);
__decorate([
    (0, common_1.Get)('matches'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get AI matches (subset of results) with pagination, sorting, and search',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Paginated list of AI matches.',
        type: ai_results_dto_1.PaginatedAiResultsResponseDto,
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_results_dto_1.GetAiResultsQueryDto]),
    __metadata("design:returntype", Promise)
], AiResultsController.prototype, "getAiMatches", null);
__decorate([
    (0, common_1.Get)('matches/count/:jobId'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get the count of AI matches for a specific job ID above a threshold',
    }),
    (0, swagger_1.ApiParam)({
        name: 'jobId',
        type: 'string',
        format: 'uuid',
        description: 'Job ID',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Number of matches.',
        type: Number,
        schema: { example: { matches: 10 } },
    }),
    __param(0, (0, common_1.Param)('jobId', common_1.ParseUUIDPipe)),
    __param(1, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, ai_results_dto_1.GetAiMatchesCountQueryDto]),
    __metadata("design:returntype", Promise)
], AiResultsController.prototype, "getAiMatchesCountByJobId", null);
__decorate([
    (0, common_1.Get)(':id'),
    (0, swagger_1.ApiOperation)({ summary: 'Get a specific AI result by its ID' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        type: 'string',
        format: 'uuid',
        description: 'AI Result ID',
    }),
    (0, swagger_1.ApiResponse)({ status: 200, description: 'The AI result.', type: ai_results_entity_1.AiResult }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'AI Result not found.' }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiResultsController.prototype, "getAiResultById", null);
__decorate([
    (0, common_1.Post)(),
    (0, swagger_1.ApiOperation)({ summary: 'Create a new AI result' }),
    (0, swagger_1.ApiResponse)({
        status: 201,
        description: 'AI result created successfully.',
        type: ai_results_entity_1.AiResult,
    }),
    (0, swagger_1.ApiResponse)({ status: 400, description: 'Invalid input data.' }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_results_dto_1.CreateAiResultDto]),
    __metadata("design:returntype", Promise)
], AiResultsController.prototype, "createAiResult", null);
__decorate([
    (0, common_1.Put)(':id'),
    (0, swagger_1.ApiOperation)({ summary: 'Update an existing AI result' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        type: 'string',
        format: 'uuid',
        description: 'AI Result ID to update',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'AI result updated successfully.',
        type: ai_results_entity_1.AiResult,
    }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'AI Result not found.' }),
    (0, swagger_1.ApiResponse)({ status: 400, description: 'Invalid input data.' }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __param(1, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, ai_results_dto_1.UpdateAiResultDto]),
    __metadata("design:returntype", Promise)
], AiResultsController.prototype, "updateAiResult", null);
__decorate([
    (0, common_1.Delete)(':id'),
    (0, common_1.HttpCode)(common_1.HttpStatus.NO_CONTENT),
    (0, swagger_1.ApiOperation)({ summary: 'Delete an AI result by its ID' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        type: 'string',
        format: 'uuid',
        description: 'AI Result ID to delete',
    }),
    (0, swagger_1.ApiResponse)({ status: 204, description: 'AI result deleted successfully.' }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'AI Result not found.' }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiResultsController.prototype, "deleteAiResult", null);
exports.AiResultsController = AiResultsController = __decorate([
    (0, swagger_1.ApiTags)('AI Results'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('ai-results'),
    __metadata("design:paramtypes", [ai_results_service_1.AiResultsService])
], AiResultsController);
//# sourceMappingURL=ai-results.controller.js.map