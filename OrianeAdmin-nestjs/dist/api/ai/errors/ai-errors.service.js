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
var AiErrorsService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AiErrorsService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const ai_errors_entity_1 = require("../../../entities/ai-errors.entity");
let AiErrorsService = AiErrorsService_1 = class AiErrorsService {
    constructor(aiErrorRepository) {
        this.aiErrorRepository = aiErrorRepository;
        this.logger = new common_1.Logger(AiErrorsService_1.name);
    }
    async getAiErrors(queryDto) {
        const { offset = 0, limit = 10, search } = queryDto;
        const query = this.aiErrorRepository.createQueryBuilder('ai_error');
        if (search) {
            query.where(`(ai_error.id::text ILIKE :search OR 
          ai_error.jobId::text ILIKE :search OR 
          ai_error.jobRunId::text ILIKE :search OR 
          ai_error.watchedVideo ILIKE :search OR 
          ai_error.error_message ILIKE :search)`, { search: `%${search}%` });
        }
        try {
            const [data, total] = await query
                .orderBy('ai_error.createdAt', 'DESC')
                .skip(offset)
                .take(limit)
                .getManyAndCount();
            return { data, total };
        }
        catch (error) {
            this.logger.error(`Error fetching AI errors: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve AI errors.');
        }
    }
    async getAiErrorById(id) {
        const error = await this.aiErrorRepository.findOne({ where: { id } });
        if (!error) {
            throw new common_1.NotFoundException(`AI Error with ID "${id}" not found.`);
        }
        return error;
    }
    async createAiError(createAiErrorDto) {
        try {
            const newError = this.aiErrorRepository.create({
                ...createAiErrorDto,
            });
            return await this.aiErrorRepository.save(newError);
        }
        catch (error) {
            this.logger.error(`Error creating AI error: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to create AI error.');
        }
    }
    async updateAiError(id, updateAiErrorDto) {
        const errorToUpdate = await this.aiErrorRepository.preload({
            id: id,
            ...updateAiErrorDto,
        });
        if (!errorToUpdate) {
            throw new common_1.NotFoundException(`AI Error with ID "${id}" not found for update.`);
        }
        try {
            return await this.aiErrorRepository.save(errorToUpdate);
        }
        catch (error) {
            this.logger.error(`Error updating AI error with ID ${id}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to update AI error.');
        }
    }
    async deleteAiError(id) {
        const result = await this.aiErrorRepository.delete(id);
        if (result.affected === 0) {
            throw new common_1.NotFoundException(`AI Error with ID "${id}" not found.`);
        }
    }
};
exports.AiErrorsService = AiErrorsService;
exports.AiErrorsService = AiErrorsService = AiErrorsService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(ai_errors_entity_1.AiError)),
    __metadata("design:paramtypes", [typeorm_2.Repository])
], AiErrorsService);
//# sourceMappingURL=ai-errors.service.js.map