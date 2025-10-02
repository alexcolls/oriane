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
exports.PaginatedAiWarningsResponseDto = exports.UpdateAiWarningDto = exports.CreateAiWarningDto = exports.GetAiWarningsQueryDto = void 0;
const swagger_1 = require("@nestjs/swagger");
const class_validator_1 = require("class-validator");
const class_transformer_1 = require("class-transformer");
const ai_warnings_entity_1 = require("../../../../entities/ai-warnings.entity");
class GetAiWarningsQueryDto {
    constructor() {
        this.offset = 0;
        this.limit = 10;
    }
}
exports.GetAiWarningsQueryDto = GetAiWarningsQueryDto;
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
], GetAiWarningsQueryDto.prototype, "offset", void 0);
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
], GetAiWarningsQueryDto.prototype, "limit", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ description: 'Search term for warnings.', required: false }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], GetAiWarningsQueryDto.prototype, "search", void 0);
class CreateAiWarningDto extends (0, swagger_1.OmitType)(ai_warnings_entity_1.AiWarning, [
    'id',
    'createdAt',
    'aiJob',
    'aiJobsRun',
]) {
}
exports.CreateAiWarningDto = CreateAiWarningDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Associated Job ID (UUID).',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsUUID)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateAiWarningDto.prototype, "jobId", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Watched video shortcode related to the warning.',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateAiWarningDto.prototype, "watchedVideo", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'The warning message text.',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateAiWarningDto.prototype, "warningMessage", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Associated Job Run ID (UUID).',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsUUID)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateAiWarningDto.prototype, "jobRunId", void 0);
class UpdateAiWarningDto extends (0, swagger_1.PartialType)(CreateAiWarningDto) {
}
exports.UpdateAiWarningDto = UpdateAiWarningDto;
class PaginatedAiWarningsResponseDto {
}
exports.PaginatedAiWarningsResponseDto = PaginatedAiWarningsResponseDto;
__decorate([
    (0, swagger_1.ApiProperty)({ type: () => [ai_warnings_entity_1.AiWarning] }),
    (0, class_validator_1.ValidateNested)({ each: true }),
    (0, class_transformer_1.Type)(() => ai_warnings_entity_1.AiWarning),
    __metadata("design:type", Array)
], PaginatedAiWarningsResponseDto.prototype, "data", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ example: 100 }),
    __metadata("design:type", Number)
], PaginatedAiWarningsResponseDto.prototype, "total", void 0);
//# sourceMappingURL=ai-warning.dto.js.map