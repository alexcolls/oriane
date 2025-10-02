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
exports.GetAiJobRunsResponseDto = exports.AiJobsRunBasicResponseDto = exports.UpdateAiJobsRunInternalDto = exports.CreateAiJobsRunInternalDto = void 0;
const swagger_1 = require("@nestjs/swagger");
const class_validator_1 = require("class-validator");
const class_transformer_1 = require("class-transformer");
const ai_jobs_run_entity_1 = require("../../../../entities/ai-jobs-run.entity");
class CreateAiJobsRunInternalDto extends (0, swagger_1.PickType)(ai_jobs_run_entity_1.AiJobsRun, [
    'jobId',
    'comparisonsToProcess',
    'state',
    'estimatedCost',
    'startedAt',
]) {
}
exports.CreateAiJobsRunInternalDto = CreateAiJobsRunInternalDto;
class UpdateAiJobsRunInternalDto extends (0, swagger_1.PartialType)((0, swagger_1.PickType)(ai_jobs_run_entity_1.AiJobsRun, [
    'comparisonsProcessed',
    'comparisonsFailed',
    'lastVideoCode',
    'lastPublishedDate',
    'finishedAt',
    'state',
    'warningsCount',
])) {
}
exports.UpdateAiJobsRunInternalDto = UpdateAiJobsRunInternalDto;
class AiJobsRunBasicResponseDto extends (0, swagger_1.PickType)(ai_jobs_run_entity_1.AiJobsRun, [
    'id',
    'createdAt',
    'jobId',
    'comparisonsToProcess',
    'comparisonsProcessed',
    'comparisonsFailed',
    'lastVideoCode',
    'lastPublishedDate',
    'startedAt',
    'finishedAt',
    'state',
    'warningsCount',
    'estimatedCost',
]) {
}
exports.AiJobsRunBasicResponseDto = AiJobsRunBasicResponseDto;
class GetAiJobRunsResponseDto {
}
exports.GetAiJobRunsResponseDto = GetAiJobRunsResponseDto;
__decorate([
    (0, swagger_1.ApiProperty)({ type: () => [AiJobsRunBasicResponseDto] }),
    (0, class_validator_1.ValidateNested)({ each: true }),
    (0, class_transformer_1.Type)(() => AiJobsRunBasicResponseDto),
    __metadata("design:type", Array)
], GetAiJobRunsResponseDto.prototype, "data", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ example: 20 }),
    __metadata("design:type", Number)
], GetAiJobRunsResponseDto.prototype, "totalInJob", void 0);
//# sourceMappingURL=ai-jobs-run.dto.js.map