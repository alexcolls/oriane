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
exports.FrameResultItemDto = exports.PaginatedAiResultsResponseDto = exports.UpdateAiResultDto = exports.CreateAiResultDto = exports.GetAiMatchesCountQueryDto = exports.GetAiResultsQueryDto = void 0;
const swagger_1 = require("@nestjs/swagger");
const class_validator_1 = require("class-validator");
const class_transformer_1 = require("class-transformer");
const ai_results_entity_1 = require("../../../../entities/ai-results.entity");
class GetAiResultsQueryDto {
    constructor() {
        this.offset = 0;
        this.limit = 10;
        this.order = 'desc';
        this.sortBy = 'createdAt';
    }
}
exports.GetAiResultsQueryDto = GetAiResultsQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Number of records to skip.',
        required: false,
        default: 0,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], GetAiResultsQueryDto.prototype, "offset", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Maximum number of records to return.',
        required: false,
        default: 10,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], GetAiResultsQueryDto.prototype, "limit", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Sort order.',
        enum: ['asc', 'desc'],
        required: false,
        default: 'desc',
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsEnum)(['asc', 'desc']),
    __metadata("design:type", String)
], GetAiResultsQueryDto.prototype, "order", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Field to sort by.',
        required: false,
        default: 'createdAt',
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], GetAiResultsQueryDto.prototype, "sortBy", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ description: 'Search term.', required: false }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], GetAiResultsQueryDto.prototype, "search", void 0);
class GetAiMatchesCountQueryDto {
    constructor() {
        this.threshold = 0.5;
    }
}
exports.GetAiMatchesCountQueryDto = GetAiMatchesCountQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Similarity threshold.',
        type: Number,
        format: 'float',
        default: 0.5,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(0),
    (0, class_validator_1.Max)(1),
    __metadata("design:type", Number)
], GetAiMatchesCountQueryDto.prototype, "threshold", void 0);
class CreateAiResultDto extends (0, swagger_1.OmitType)(ai_results_entity_1.AiResult, [
    'id',
    'createdAt',
    'aiJob',
    'aiJobsRun',
]) {
}
exports.CreateAiResultDto = CreateAiResultDto;
__decorate([
    (0, swagger_1.ApiProperty)(),
    (0, class_validator_1.IsUUID)(),
    __metadata("design:type", String)
], CreateAiResultDto.prototype, "jobId", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    (0, class_validator_1.IsUUID)(),
    __metadata("design:type", String)
], CreateAiResultDto.prototype, "jobRunId", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], CreateAiResultDto.prototype, "model", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], CreateAiResultDto.prototype, "monitoredVideo", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], CreateAiResultDto.prototype, "watchedVideo", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ type: 'number', format: 'float' }),
    (0, class_validator_1.IsNumber)(),
    __metadata("design:type", Number)
], CreateAiResultDto.prototype, "similarity", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ type: 'number', format: 'float' }),
    (0, class_validator_1.IsNumber)(),
    __metadata("design:type", Number)
], CreateAiResultDto.prototype, "avgSimilarity", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ type: 'number', format: 'float' }),
    (0, class_validator_1.IsNumber)(),
    __metadata("design:type", Number)
], CreateAiResultDto.prototype, "stdSimilarity", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ type: 'number', format: 'float' }),
    (0, class_validator_1.IsNumber)(),
    __metadata("design:type", Number)
], CreateAiResultDto.prototype, "maxSimilarity", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Array of frame numbers and their similarity scores',
        type: () => [FrameResultItemDto],
        isArray: true,
    }),
    (0, class_validator_1.IsArray)(),
    (0, class_validator_1.ValidateNested)({ each: true }),
    (0, class_transformer_1.Type)(() => FrameResultItemDto),
    __metadata("design:type", Array)
], CreateAiResultDto.prototype, "frameResults", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ type: 'number', format: 'float' }),
    (0, class_validator_1.IsNumber)(),
    __metadata("design:type", Number)
], CreateAiResultDto.prototype, "processedInSecs", void 0);
class UpdateAiResultDto extends (0, swagger_1.PartialType)(CreateAiResultDto) {
}
exports.UpdateAiResultDto = UpdateAiResultDto;
class PaginatedAiResultsResponseDto {
}
exports.PaginatedAiResultsResponseDto = PaginatedAiResultsResponseDto;
__decorate([
    (0, swagger_1.ApiProperty)({ type: () => [ai_results_entity_1.AiResult] }),
    (0, class_validator_1.ValidateNested)({ each: true }),
    (0, class_transformer_1.Type)(() => ai_results_entity_1.AiResult),
    __metadata("design:type", Array)
], PaginatedAiResultsResponseDto.prototype, "data", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ example: 100 }),
    __metadata("design:type", Number)
], PaginatedAiResultsResponseDto.prototype, "total", void 0);
class FrameResultItemDto {
}
exports.FrameResultItemDto = FrameResultItemDto;
__decorate([
    (0, swagger_1.ApiProperty)({ description: 'Frame number', example: 1 }),
    (0, class_validator_1.IsInt)(),
    __metadata("design:type", Number)
], FrameResultItemDto.prototype, "frame_number", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Similarity score for the frame',
        example: 0.95,
        type: 'number',
        format: 'float',
    }),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(0),
    (0, class_validator_1.Max)(1),
    __metadata("design:type", Number)
], FrameResultItemDto.prototype, "similarity", void 0);
//# sourceMappingURL=ai-results.dto.js.map