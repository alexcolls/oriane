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
Object.defineProperty(exports, "__esModule", { value: true });
exports.GetMonitoredVideosResponseDto = exports.MonitoredVideoGroupDto = exports.MonitoredVideoCodeDetailsDto = exports.RunJobResultDto = exports.GetAiJobsResponseDto = exports.AiJobBasicResponseDto = exports.GetAiJobsQueryDto = exports.UpdateAiJobDto = exports.QueueAiJobDto = void 0;
const swagger_1 = require("@nestjs/swagger");
const class_validator_1 = require("class-validator");
const class_transformer_1 = require("class-transformer");
const models_1 = require("../../../../models/models");
const ai_jobs_entity_1 = require("../../../../entities/ai-jobs.entity");
class QueueAiJobDto {
    constructor() {
        this.useGpu = false;
    }
}
exports.QueueAiJobDto = QueueAiJobDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Shortcode of the video to be monitored.',
        example: 'CXYZ123ABC',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], QueueAiJobDto.prototype, "monitoredVideo", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'AI model to be used.',
        enum: models_1.MODELS,
        example: 'SSCD',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    (0, class_validator_1.IsIn)(models_1.MODELS),
    __metadata("design:type", String)
], QueueAiJobDto.prototype, "model", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Whether to use GPU for processing.',
        default: false,
        required: false,
    }),
    (0, class_validator_1.IsBoolean)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Boolean)
], QueueAiJobDto.prototype, "useGpu", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Threshold for the AI model.',
        default: 0.5,
        required: false,
        type: 'number',
        format: 'float',
    }),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(0),
    (0, class_validator_1.Max)(1),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Number)
], QueueAiJobDto.prototype, "threshold", void 0);
class UpdateAiJobDto extends (0, swagger_1.PartialType)((0, swagger_1.PickType)(ai_jobs_entity_1.AiJob, ['threshold', 'useGpu', 'model'])) {
}
exports.UpdateAiJobDto = UpdateAiJobDto;
class GetAiJobsQueryDto {
    constructor() {
        this.offset = 0;
        this.limit = 10;
    }
}
exports.GetAiJobsQueryDto = GetAiJobsQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Number of records to skip.',
        required: false,
        default: 0,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], GetAiJobsQueryDto.prototype, "offset", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Maximum number of records to return.',
        required: false,
        default: 10,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], GetAiJobsQueryDto.prototype, "limit", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Search term (e.g., by monitoredVideo or model).',
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], GetAiJobsQueryDto.prototype, "search", void 0);
class AiJobBasicResponseDto extends (0, swagger_1.PickType)(ai_jobs_entity_1.AiJob, [
    'id',
    'createdAt',
    'model',
    'useGpu',
    'monitoredVideo',
    'publishedDate',
    'threshold',
]) {
}
exports.AiJobBasicResponseDto = AiJobBasicResponseDto;
class GetAiJobsResponseDto {
}
exports.GetAiJobsResponseDto = GetAiJobsResponseDto;
__decorate([
    (0, swagger_1.ApiProperty)({ type: () => [AiJobBasicResponseDto] }),
    (0, class_validator_1.ValidateNested)({ each: true }),
    (0, class_transformer_1.Type)(() => AiJobBasicResponseDto),
    __metadata("design:type", Array)
], GetAiJobsResponseDto.prototype, "data", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ example: 100 }),
    __metadata("design:type", Number)
], GetAiJobsResponseDto.prototype, "total", void 0);
class RunJobResultDto {
}
exports.RunJobResultDto = RunJobResultDto;
__decorate([
    (0, swagger_1.ApiProperty)(),
    __metadata("design:type", String)
], RunJobResultDto.prototype, "jobId", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    __metadata("design:type", String)
], RunJobResultDto.prototype, "runId", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    __metadata("design:type", Number)
], RunJobResultDto.prototype, "totalVideosFound", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    __metadata("design:type", Number)
], RunJobResultDto.prototype, "videosDispatched", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    __metadata("design:type", String)
], RunJobResultDto.prototype, "finalRunState", void 0);
class MonitoredVideoCodeDetailsDto {
}
exports.MonitoredVideoCodeDetailsDto = MonitoredVideoCodeDetailsDto;
__decorate([
    (0, swagger_1.ApiProperty)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], MonitoredVideoCodeDetailsDto.prototype, "code", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    (0, class_validator_1.IsBoolean)(),
    __metadata("design:type", Boolean)
], MonitoredVideoCodeDetailsDto.prototype, "is_extracted", void 0);
class MonitoredVideoGroupDto {
}
exports.MonitoredVideoGroupDto = MonitoredVideoGroupDto;
__decorate([
    (0, swagger_1.ApiProperty)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], MonitoredVideoGroupDto.prototype, "username", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ type: () => [MonitoredVideoCodeDetailsDto] }),
    (0, class_validator_1.ValidateNested)({ each: true }),
    (0, class_transformer_1.Type)(() => MonitoredVideoCodeDetailsDto),
    __metadata("design:type", Array)
], MonitoredVideoGroupDto.prototype, "video_codes", void 0);
class GetMonitoredVideosResponseDto {
}
exports.GetMonitoredVideosResponseDto = GetMonitoredVideosResponseDto;
__decorate([
    (0, swagger_1.ApiProperty)({ type: () => [MonitoredVideoGroupDto] }),
    (0, class_validator_1.ValidateNested)({ each: true }),
    (0, class_transformer_1.Type)(() => MonitoredVideoGroupDto),
    __metadata("design:type", Array)
], GetMonitoredVideosResponseDto.prototype, "data", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    (0, class_validator_1.IsInt)(),
    __metadata("design:type", Number)
], GetMonitoredVideosResponseDto.prototype, "total", void 0);
//# sourceMappingURL=ai-jobs.dto.js.map