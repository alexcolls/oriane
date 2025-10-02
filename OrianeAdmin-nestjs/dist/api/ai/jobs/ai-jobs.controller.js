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
var AiJobsController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AiJobsController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const ai_jobs_service_1 = require("./ai-jobs.service");
const ai_jobs_dto_1 = require("./dto/ai-jobs.dto");
const ai_jobs_run_dto_1 = require("./dto/ai-jobs-run.dto");
let AiJobsController = AiJobsController_1 = class AiJobsController {
    constructor(aiJobsService) {
        this.aiJobsService = aiJobsService;
        this.logger = new common_1.Logger(AiJobsController_1.name);
    }
    async startJobWorkflow(dto) {
        this.logger.log(`Request to start job workflow for video: ${dto.monitoredVideo}, model: ${dto.model}`);
        return this.aiJobsService.startJobWorkflow(dto);
    }
    async getAiJobDefinitions(queryDto) {
        return this.aiJobsService.getAiJobs(queryDto);
    }
    async getAiJobDetails(id) {
        return this.aiJobsService.getAiJobDetails(id);
    }
    async getAiJobsByMonitoredVideoCode(code) {
        return this.aiJobsService.getAiJobsByMonitoredVideoCode(code);
    }
    async patchAiJobDefinition(id, updateDto) {
        return this.aiJobsService.updateAiJobDefinition(id, updateDto);
    }
    async deleteAiJob(id) {
        await this.aiJobsService.deleteAiJob(id);
    }
    async getAllRunsForJob(jobId, queryDto) {
        return this.aiJobsService.getAllRunsForJob(jobId, queryDto);
    }
    async getSpecificAiJobRun(jobId, runId) {
        return this.aiJobsService.getSpecificAiJobRun(jobId, runId);
    }
    async getVideosToCompareStatsByMonitoredVideo(shortcode) {
        return await this.aiJobsService.getVideosToCompareStatsByMonitoredVideo(shortcode);
    }
    async getMonitoredContentGroupedByUser(queryDto) {
        return await this.aiJobsService.getMonitoredContentGroupedByUser(queryDto);
    }
    async updateAiJobThreshold(id, updateDto) {
        return this.aiJobsService.updateJobThreshold(id, updateDto);
    }
    async getJobThresholdValue(id) {
        return await this.aiJobsService.getJobThresholdValue(id);
    }
    async getAggregatedEstimatedCostForJob(id) {
        return await this.aiJobsService.getAggregatedEstimatedCostForJob(id);
    }
    async getSpecificJobRunEstimatedCost(runId) {
        return await this.aiJobsService.getSpecificJobRunEstimatedCost(runId);
    }
    async getUsernameOfMonitoredVideoForJob(id) {
        return await this.aiJobsService.getUsernameOfMonitoredVideoForJob(id);
    }
    async getJobDefinitionPublishedDate(id) {
        return await this.aiJobsService.getJobDefinitionPublishedDate(id);
    }
    async getNewContentStatsRelativeToJobDate(id) {
        return await this.aiJobsService.getNewContentStatsRelativeToJobDate(id);
    }
    async getAllActiveJobsThresholds() {
        return await this.aiJobsService.getAllActiveJobsThresholds();
    }
    async calculateEstimatedCostByComparisons(comparisons) {
        return this.aiJobsService.calculateEstimatedCostByComparisons(comparisons);
    }
};
exports.AiJobsController = AiJobsController;
__decorate([
    (0, common_1.Post)('start-workflow'),
    (0, swagger_1.ApiOperation)({
        summary: 'Start a new AI job workflow (creates AiJob and first AiJobsRun)',
    }),
    (0, swagger_1.ApiBody)({ type: ai_jobs_dto_1.QueueAiJobDto }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.CREATED,
        description: 'AI job and first run created successfully.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.CONFLICT,
        description: 'Duplicate job definition.',
    }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_jobs_dto_1.QueueAiJobDto]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "startJobWorkflow", null);
__decorate([
    (0, common_1.Get)(),
    (0, swagger_1.ApiOperation)({ summary: 'Get all AI job definitions' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'List of AI job definitions.',
        type: ai_jobs_dto_1.GetAiJobsResponseDto,
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_jobs_dto_1.GetAiJobsQueryDto]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getAiJobDefinitions", null);
__decorate([
    (0, common_1.Get)('by-id/:id'),
    (0, swagger_1.ApiOperation)({ summary: 'Get an AI job definition by its ID' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'UUID of the AiJob definition',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'AI job definition retrieved successfully.',
        type: ai_jobs_dto_1.AiJobBasicResponseDto,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI job definition not found',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getAiJobDetails", null);
__decorate([
    (0, common_1.Get)('code/:code'),
    (0, swagger_1.ApiOperation)({ summary: 'Get AI job definitions by monitored video code' }),
    (0, swagger_1.ApiParam)({ name: 'code', description: 'Monitored video code', type: String }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'List of AI job definitions for the code.',
        type: [ai_jobs_dto_1.AiJobBasicResponseDto],
    }),
    __param(0, (0, common_1.Param)('code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getAiJobsByMonitoredVideoCode", null);
__decorate([
    (0, common_1.Patch)(':id/definition'),
    (0, swagger_1.ApiOperation)({
        summary: 'Partially update an AI job definition (e.g., threshold, model, useGpu)',
    }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'UUID of the AiJob definition to update',
        type: String,
    }),
    (0, swagger_1.ApiBody)({ type: ai_jobs_dto_1.UpdateAiJobDto }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'AI job definition updated successfully.',
        type: ai_jobs_dto_1.AiJobBasicResponseDto,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI job not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __param(1, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, ai_jobs_dto_1.UpdateAiJobDto]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "patchAiJobDefinition", null);
__decorate([
    (0, common_1.Delete)(':id'),
    (0, common_1.HttpCode)(common_1.HttpStatus.NO_CONTENT),
    (0, swagger_1.ApiOperation)({
        summary: 'Delete an AI job definition (and its runs if cascaded)',
    }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'UUID of the AiJob definition to delete',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NO_CONTENT,
        description: 'AI job definition deleted successfully',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI job not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "deleteAiJob", null);
__decorate([
    (0, common_1.Get)(':jobId/runs'),
    (0, swagger_1.ApiOperation)({ summary: 'Get all runs for a specific AI job' }),
    (0, swagger_1.ApiParam)({
        name: 'jobId',
        description: 'UUID of the parent AiJob',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'List of all runs for the job.',
        type: ai_jobs_run_dto_1.GetAiJobRunsResponseDto,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'Parent AiJob not found.',
    }),
    __param(0, (0, common_1.Param)('jobId', common_1.ParseUUIDPipe)),
    __param(1, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, ai_jobs_dto_1.GetAiJobsQueryDto]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getAllRunsForJob", null);
__decorate([
    (0, common_1.Get)(':jobId/runs/:runId'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get a specific AI job run by its ID and parent job ID',
    }),
    (0, swagger_1.ApiParam)({
        name: 'jobId',
        description: 'UUID of the parent AiJob',
        type: String,
    }),
    (0, swagger_1.ApiParam)({
        name: 'runId',
        description: 'UUID of the AiJobsRun',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'AI job run details retrieved successfully.',
        type: ai_jobs_run_dto_1.AiJobsRunBasicResponseDto,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Job or Job Run not found.',
    }),
    __param(0, (0, common_1.Param)('jobId', common_1.ParseUUIDPipe)),
    __param(1, (0, common_1.Param)('runId', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getSpecificAiJobRun", null);
__decorate([
    (0, common_1.Get)('stats/videos-to-compare/:shortcode'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get statistics of videos to compare against a monitored video shortcode',
    }),
    (0, swagger_1.ApiParam)({
        name: 'shortcode',
        description: 'The shortcode of the monitored video',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Statistics retrieved successfully.',
    }),
    __param(0, (0, common_1.Param)('shortcode')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getVideosToCompareStatsByMonitoredVideo", null);
__decorate([
    (0, common_1.Get)('stats/monitored-content-groups'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get monitored content video codes, grouped by username',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Grouped monitored content retrieved successfully.',
        type: ai_jobs_dto_1.GetMonitoredVideosResponseDto,
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_jobs_dto_1.GetAiJobsQueryDto]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getMonitoredContentGroupedByUser", null);
__decorate([
    (0, common_1.Patch)(':id/update-threshold'),
    (0, swagger_1.ApiOperation)({
        summary: 'Update an AI job threshold',
    }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'UUID of the AiJob definition to update',
        type: String,
    }),
    (0, swagger_1.ApiBody)({ type: ai_jobs_dto_1.UpdateAiJobDto }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'AI job definition updated successfully.',
        type: ai_jobs_dto_1.AiJobBasicResponseDto,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI job not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __param(1, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "updateAiJobThreshold", null);
__decorate([
    (0, common_1.Get)(':id/threshold'),
    (0, swagger_1.ApiOperation)({ summary: 'Get the threshold for a specific AI job' }),
    (0, swagger_1.ApiParam)({ name: 'id', description: 'UUID of the AiJob', type: String }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Threshold retrieved successfully.',
        type: Number,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Job not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getJobThresholdValue", null);
__decorate([
    (0, common_1.Get)(':id/aggregated-cost'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get total aggregated estimated cost for an AI job (sum of its runs)',
    }),
    (0, swagger_1.ApiParam)({ name: 'id', description: 'UUID of the AiJob', type: String }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Aggregated estimated cost retrieved successfully.',
        type: Number,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Job not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getAggregatedEstimatedCostForJob", null);
__decorate([
    (0, common_1.Get)('run/:runId/estimated-cost'),
    (0, swagger_1.ApiOperation)({ summary: 'Get estimated cost for a specific AI job run' }),
    (0, swagger_1.ApiParam)({
        name: 'runId',
        description: 'UUID of the AiJobsRun',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Estimated cost for the run retrieved successfully.',
        type: Number,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Job Run not found.',
    }),
    __param(0, (0, common_1.Param)('runId', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getSpecificJobRunEstimatedCost", null);
__decorate([
    (0, common_1.Get)(':id/username'),
    (0, swagger_1.ApiOperation)({ summary: 'Get monitored content username for an AI job' }),
    (0, swagger_1.ApiParam)({ name: 'id', description: 'UUID of the AiJob', type: String }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Monitored content username retrieved successfully.',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Job or related content not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getUsernameOfMonitoredVideoForJob", null);
__decorate([
    (0, common_1.Get)(':id/published-date'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get the original published date of the monitored video for an AI job definition',
    }),
    (0, swagger_1.ApiParam)({ name: 'id', description: 'UUID of the AiJob', type: String }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Published date retrieved successfully.',
        type: Date,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Job not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getJobDefinitionPublishedDate", null);
__decorate([
    (0, common_1.Get)(':id/new-contents'),
    (0, swagger_1.ApiOperation)({
        summary: "Get statistics of new content relative to an AI job's monitored video publish date",
    }),
    (0, swagger_1.ApiParam)({ name: 'id', description: 'UUID of the AiJob', type: String }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'New content statistics retrieved successfully.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Job not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getNewContentStatsRelativeToJobDate", null);
__decorate([
    (0, common_1.Get)('thresholds/all-active'),
    (0, swagger_1.ApiOperation)({ summary: 'Get thresholds for all active AI jobs' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'All active jobs thresholds retrieved successfully.',
        type: Object,
    }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "getAllActiveJobsThresholds", null);
__decorate([
    (0, common_1.Get)('costs/estimate-by-comparisons'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get estimated cost based on number of comparisons',
    }),
    (0, swagger_1.ApiQuery)({ name: 'comparisons', type: Number, required: true }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Estimated cost retrieved successfully.',
        type: Number,
    }),
    __param(0, (0, common_1.Query)('comparisons', common_1.ParseIntPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Number]),
    __metadata("design:returntype", Promise)
], AiJobsController.prototype, "calculateEstimatedCostByComparisons", null);
exports.AiJobsController = AiJobsController = AiJobsController_1 = __decorate([
    (0, swagger_1.ApiTags)('AI Jobs'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('ai-jobs'),
    __metadata("design:paramtypes", [ai_jobs_service_1.AiJobsService])
], AiJobsController);
//# sourceMappingURL=ai-jobs.controller.js.map