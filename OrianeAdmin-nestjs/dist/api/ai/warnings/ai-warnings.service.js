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
var AiWarningsService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AiWarningsService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const ai_warnings_entity_1 = require("../../../entities/ai-warnings.entity");
let AiWarningsService = AiWarningsService_1 = class AiWarningsService {
    constructor(aiWarningRepository) {
        this.aiWarningRepository = aiWarningRepository;
        this.logger = new common_1.Logger(AiWarningsService_1.name);
    }
    async getAiWarnings(offset, limit, search) {
        try {
            const queryBuilder = this.aiWarningRepository.createQueryBuilder('warning');
            if (search) {
                queryBuilder.where(new typeorm_2.Brackets((qb) => {
                    qb.where('warning.id::text ILIKE :search', {
                        search: `%${search}%`,
                    })
                        .orWhere('warning.jobId::text ILIKE :search', {
                        search: `%${search}%`,
                    })
                        .orWhere('warning.jobRunId::text ILIKE :search', {
                        search: `%${search}%`,
                    })
                        .orWhere('warning.watchedVideo ILIKE :search', {
                        search: `%${search}%`,
                    })
                        .orWhere('warning.warningMessage ILIKE :search', {
                        search: `%${search}%`,
                    });
                }));
            }
            const [data, total] = await queryBuilder
                .orderBy('warning.createdAt', 'DESC')
                .skip(offset)
                .take(limit)
                .getManyAndCount();
            return { data, total };
        }
        catch (error) {
            this.logger.error(`Error fetching AI warnings: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve AI warnings.');
        }
    }
    async getAiWarningById(id) {
        const warning = await this.aiWarningRepository.findOneBy({ id });
        if (!warning) {
            throw new common_1.NotFoundException(`AI Warning with ID ${id} not found.`);
        }
        return warning;
    }
    async createAiWarning(payload) {
        try {
            const newWarning = this.aiWarningRepository.create(payload);
            return await this.aiWarningRepository.save(newWarning);
        }
        catch (error) {
            this.logger.error(`Error creating AI Warning: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to create AI Warning.');
        }
    }
    async updateAiWarning(id, payload) {
        const warningToUpdate = await this.aiWarningRepository.preload({
            id: id,
            ...payload,
        });
        if (!warningToUpdate) {
            throw new common_1.NotFoundException(`AI Warning with ID ${id} not found for update.`);
        }
        try {
            return await this.aiWarningRepository.save(warningToUpdate);
        }
        catch (error) {
            this.logger.error(`Error updating AI Warning ${id}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to update AI Warning.');
        }
    }
    async deleteAiWarning(id) {
        const result = await this.aiWarningRepository.delete(id);
        if (result.affected === 0) {
            throw new common_1.NotFoundException(`AI Warning with ID ${id} not found for deletion.`);
        }
    }
};
exports.AiWarningsService = AiWarningsService;
exports.AiWarningsService = AiWarningsService = AiWarningsService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(ai_warnings_entity_1.AiWarning)),
    __metadata("design:paramtypes", [typeorm_2.Repository])
], AiWarningsService);
//# sourceMappingURL=ai-warnings.service.js.map