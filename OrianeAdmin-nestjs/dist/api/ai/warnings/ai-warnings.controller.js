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
exports.AiWarningsController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const ai_warnings_service_1 = require("./ai-warnings.service");
const ai_warnings_entity_1 = require("../../../entities/ai-warnings.entity");
const ai_warning_dto_1 = require("./dto/ai-warning.dto");
let AiWarningsController = class AiWarningsController {
    constructor(aiWarningsService) {
        this.aiWarningsService = aiWarningsService;
    }
    async getAiWarnings(queryDto) {
        return this.aiWarningsService.getAiWarnings(queryDto.offset ?? 0, queryDto.limit ?? 10, queryDto.search);
    }
    async getAiWarningById(id) {
        return this.aiWarningsService.getAiWarningById(id);
    }
    async createAiWarning(createDto) {
        return this.aiWarningsService.createAiWarning(createDto);
    }
    async updateAiWarning(id, updateDto) {
        return this.aiWarningsService.updateAiWarning(id, updateDto);
    }
    async deleteAiWarning(id) {
        await this.aiWarningsService.deleteAiWarning(id);
    }
};
exports.AiWarningsController = AiWarningsController;
__decorate([
    (0, common_1.Get)(),
    (0, swagger_1.ApiOperation)({ summary: 'Get all AI warnings with pagination and search' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Paginated list of AI warnings.',
        type: ai_warning_dto_1.PaginatedAiWarningsResponseDto,
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_warning_dto_1.GetAiWarningsQueryDto]),
    __metadata("design:returntype", Promise)
], AiWarningsController.prototype, "getAiWarnings", null);
__decorate([
    (0, common_1.Get)(':id'),
    (0, swagger_1.ApiOperation)({ summary: 'Get a specific AI warning by its ID' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        type: 'string',
        format: 'uuid',
        description: 'AI Warning ID',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'The AI warning.',
        type: ai_warnings_entity_1.AiWarning,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Warning not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiWarningsController.prototype, "getAiWarningById", null);
__decorate([
    (0, common_1.Post)(),
    (0, swagger_1.ApiOperation)({ summary: 'Create a new AI warning' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.CREATED,
        description: 'AI warning created successfully.',
        type: ai_warnings_entity_1.AiWarning,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input data.',
    }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_warning_dto_1.CreateAiWarningDto]),
    __metadata("design:returntype", Promise)
], AiWarningsController.prototype, "createAiWarning", null);
__decorate([
    (0, common_1.Put)(':id'),
    (0, swagger_1.ApiOperation)({ summary: 'Update an existing AI warning' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        type: 'string',
        format: 'uuid',
        description: 'AI Warning ID to update',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'AI warning updated successfully.',
        type: ai_warnings_entity_1.AiWarning,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Warning not found.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input data.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __param(1, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, ai_warning_dto_1.UpdateAiWarningDto]),
    __metadata("design:returntype", Promise)
], AiWarningsController.prototype, "updateAiWarning", null);
__decorate([
    (0, common_1.Delete)(':id'),
    (0, common_1.HttpCode)(common_1.HttpStatus.NO_CONTENT),
    (0, swagger_1.ApiOperation)({ summary: 'Delete an AI warning by its ID' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        type: 'string',
        format: 'uuid',
        description: 'AI Warning ID to delete',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NO_CONTENT,
        description: 'AI warning deleted successfully.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'AI Warning not found.',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiWarningsController.prototype, "deleteAiWarning", null);
exports.AiWarningsController = AiWarningsController = __decorate([
    (0, swagger_1.ApiTags)('AI Warnings'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('ai-warnings'),
    __metadata("design:paramtypes", [ai_warnings_service_1.AiWarningsService])
], AiWarningsController);
//# sourceMappingURL=ai-warnings.controller.js.map