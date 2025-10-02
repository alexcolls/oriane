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
exports.GetAiErrorsResponseDto = exports.GetAiErrorsQueryDto = exports.UpdateAiErrorDto = exports.CreateAiErrorDto = void 0;
const swagger_1 = require("@nestjs/swagger");
const class_validator_1 = require("class-validator");
const ai_errors_entity_1 = require("../../../../entities/ai-errors.entity");
class CreateAiErrorDto {
}
exports.CreateAiErrorDto = CreateAiErrorDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'El ID del InstaContent relacionado (job_id en la entidad).',
        example: 'a1b2c3d4-e5f6-7890-1234-567890abcdef',
    }),
    (0, class_validator_1.IsUUID)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], CreateAiErrorDto.prototype, "jobId", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Identificador del vídeo que se estaba procesando.',
        example: 'video_shortcode_xyz',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], CreateAiErrorDto.prototype, "watchedVideo", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Mensaje de error detallado.',
        example: 'Timeout al procesar el frame 123.',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], CreateAiErrorDto.prototype, "error_message", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'ID opcional de la ejecución específica del job.',
        example: 'b2c3d4e5-f6g7-8901-2345-678901bcdef0',
        required: false,
    }),
    (0, class_validator_1.IsUUID)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateAiErrorDto.prototype, "jobRunId", void 0);
class UpdateAiErrorDto extends (0, swagger_1.PartialType)(CreateAiErrorDto) {
}
exports.UpdateAiErrorDto = UpdateAiErrorDto;
class GetAiErrorsQueryDto {
    constructor() {
        this.offset = 0;
        this.limit = 10;
    }
}
exports.GetAiErrorsQueryDto = GetAiErrorsQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Número de registros a omitir (para paginación).',
        required: false,
        default: 0,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], GetAiErrorsQueryDto.prototype, "offset", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Número máximo de registros a devolver.',
        required: false,
        default: 10,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], GetAiErrorsQueryDto.prototype, "limit", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Término de búsqueda para filtrar errores.',
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], GetAiErrorsQueryDto.prototype, "search", void 0);
class GetAiErrorsResponseDto {
}
exports.GetAiErrorsResponseDto = GetAiErrorsResponseDto;
__decorate([
    (0, swagger_1.ApiProperty)({ type: () => [ai_errors_entity_1.AiError] }),
    __metadata("design:type", Array)
], GetAiErrorsResponseDto.prototype, "data", void 0);
__decorate([
    (0, swagger_1.ApiProperty)(),
    __metadata("design:type", Number)
], GetAiErrorsResponseDto.prototype, "total", void 0);
//# sourceMappingURL=ai-errors.dto.js.map