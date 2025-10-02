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
exports.AiErrorsController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const ai_errors_service_1 = require("./ai-errors.service");
const ai_errors_dto_1 = require("./dto/ai-errors.dto");
const ai_errors_entity_1 = require("../../../entities/ai-errors.entity");
let AiErrorsController = class AiErrorsController {
    constructor(aiErrorsService) {
        this.aiErrorsService = aiErrorsService;
    }
    async getAiErrors(queryDto) {
        return this.aiErrorsService.getAiErrors(queryDto);
    }
    async getAiErrorById(id) {
        return this.aiErrorsService.getAiErrorById(id);
    }
    async createAiError(createAiErrorDto) {
        return this.aiErrorsService.createAiError(createAiErrorDto);
    }
    async updateAiError(id, updateAiErrorDto) {
        return this.aiErrorsService.updateAiError(id, updateAiErrorDto);
    }
    async deleteAiError(id) {
        await this.aiErrorsService.deleteAiError(id);
    }
};
exports.AiErrorsController = AiErrorsController;
__decorate([
    (0, common_1.Get)(),
    (0, swagger_1.ApiOperation)({ summary: 'Obtener una lista paginada de errores de IA' }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Lista de errores de IA y el total.',
        type: ai_errors_dto_1.GetAiErrorsResponseDto,
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_errors_dto_1.GetAiErrorsQueryDto]),
    __metadata("design:returntype", Promise)
], AiErrorsController.prototype, "getAiErrors", null);
__decorate([
    (0, common_1.Get)(':id'),
    (0, swagger_1.ApiOperation)({ summary: 'Obtener un error de IA por su ID' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'El UUID del error de IA',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'El error de IA encontrado.',
        type: ai_errors_entity_1.AiError,
    }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'Error de IA no encontrado.' }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiErrorsController.prototype, "getAiErrorById", null);
__decorate([
    (0, common_1.Post)(),
    (0, swagger_1.ApiOperation)({ summary: 'Crear un nuevo error de IA' }),
    (0, swagger_1.ApiResponse)({
        status: 201,
        description: 'El error de IA ha sido creado exitosamente.',
        type: ai_errors_entity_1.AiError,
    }),
    (0, swagger_1.ApiResponse)({ status: 400, description: 'Datos de entrada inválidos.' }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [ai_errors_dto_1.CreateAiErrorDto]),
    __metadata("design:returntype", Promise)
], AiErrorsController.prototype, "createAiError", null);
__decorate([
    (0, common_1.Put)(':id'),
    (0, swagger_1.ApiOperation)({ summary: 'Actualizar un error de IA existente' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'El UUID del error de IA a actualizar',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'El error de IA ha sido actualizado exitosamente.',
        type: ai_errors_entity_1.AiError,
    }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'Error de IA no encontrado.' }),
    (0, swagger_1.ApiResponse)({ status: 400, description: 'Datos de entrada inválidos.' }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __param(1, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, ai_errors_dto_1.UpdateAiErrorDto]),
    __metadata("design:returntype", Promise)
], AiErrorsController.prototype, "updateAiError", null);
__decorate([
    (0, common_1.Delete)(':id'),
    (0, common_1.HttpCode)(common_1.HttpStatus.NO_CONTENT),
    (0, swagger_1.ApiOperation)({ summary: 'Eliminar un error de IA por su ID' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'El UUID del error de IA a eliminar',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: 204,
        description: 'El error de IA ha sido eliminado exitosamente.',
    }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'Error de IA no encontrado.' }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], AiErrorsController.prototype, "deleteAiError", null);
exports.AiErrorsController = AiErrorsController = __decorate([
    (0, swagger_1.ApiTags)('AI Errors'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('ai-errors'),
    __metadata("design:paramtypes", [ai_errors_service_1.AiErrorsService])
], AiErrorsController);
//# sourceMappingURL=ai-errors.controller.js.map