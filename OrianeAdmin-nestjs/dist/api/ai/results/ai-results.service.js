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
var AiResultsService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AiResultsService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const ai_results_entity_1 = require("../../../entities/ai-results.entity");
const database_service_1 = require("../../../database/database.service");
let AiResultsService = AiResultsService_1 = class AiResultsService {
    constructor(aiResultRepository, databaseService) {
        this.aiResultRepository = aiResultRepository;
        this.databaseService = databaseService;
        this.logger = new common_1.Logger(AiResultsService_1.name);
    }
    async getAiResults(offset, limit, order, sortBy, search) {
        try {
            const result = await this.databaseService.executeQuery('SELECT search_ai_results($1, $2, $3, $4, $5) as result', [search || '', limit, offset, sortBy || 'createdAt', order || 'desc']);
            if (result?.length > 0 && result[0].result) {
                const parsedResult = result[0].result;
                return {
                    data: parsedResult.rows || [],
                    total: parsedResult.total || 0,
                };
            }
            return { data: [], total: 0 };
        }
        catch (error) {
            this.logger.error(`Error calling search_ai_results RPC: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve AI results via RPC.');
        }
    }
    async getAiMatches(offset, limit, order, sortBy, search) {
        try {
            const result = await this.databaseService.executeQuery('SELECT search_ai_matches($1, $2, $3, $4, $5) as result', [offset, limit, search || '', sortBy || 'created_at', order || 'desc']);
            if (result?.length > 0 && result[0].result) {
                const parsedResult = result[0].result;
                return {
                    data: parsedResult.rows || [],
                    total: parsedResult.total || 0,
                };
            }
            return { data: [], total: 0 };
        }
        catch (error) {
            this.logger.error(`Error calling search_ai_matches RPC: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve AI matches via RPC.');
        }
    }
    async getAiMatchesCountByJobId(jobId, threshold) {
        try {
            const result = await this.databaseService.executeQuery('SELECT count_high_similarity_for_job($1, $2) as match_count', [jobId, threshold]);
            if (result &&
                result.length > 0 &&
                typeof result[0].match_count === 'number') {
                return { matches: result[0].match_count };
            }
            this.logger.warn(`RPC count_high_similarity_for_job for job ${jobId} returned unexpected data or no count.`);
            return { matches: 0 };
        }
        catch (error) {
            this.logger.error(`Error calling count_high_similarity_for_job RPC for job ${jobId}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve AI matches count for job via RPC.');
        }
    }
    async getAiResultById(id) {
        const result = await this.aiResultRepository.findOneBy({ id });
        if (!result) {
            throw new common_1.NotFoundException(`AI Result with ID ${id} not found.`);
        }
        return result;
    }
    async createAiResult(payload) {
        try {
            const newResult = this.aiResultRepository.create(payload);
            return await this.aiResultRepository.save(newResult);
        }
        catch (error) {
            this.logger.error(`Error creating AI Result: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to create AI Result.');
        }
    }
    async updateAiResult(id, payload) {
        const resultToUpdate = await this.aiResultRepository.preload({
            id: id,
            ...payload,
        });
        if (!resultToUpdate) {
            throw new common_1.NotFoundException(`AI Result with ID ${id} not found for update.`);
        }
        try {
            return await this.aiResultRepository.save(resultToUpdate);
        }
        catch (error) {
            this.logger.error(`Error updating AI Result ${id}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to update AI Result.');
        }
    }
    async deleteAiResult(id) {
        const result = await this.aiResultRepository.delete(id);
        if (result.affected === 0) {
            throw new common_1.NotFoundException(`AI Result with ID ${id} not found for deletion.`);
        }
    }
};
exports.AiResultsService = AiResultsService;
exports.AiResultsService = AiResultsService = AiResultsService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(ai_results_entity_1.AiResult)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        database_service_1.DatabaseService])
], AiResultsService);
//# sourceMappingURL=ai-results.service.js.map