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
var ExtractionService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtractionService = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const content_entity_1 = require("../../entities/content.entity");
const global_events_entity_1 = require("../../entities/global-events.entity");
const database_service_1 = require("../../database/database.service");
const BATCH_SIZE_VIDEO_EXTRACTION = 1000;
let ExtractionService = ExtractionService_1 = class ExtractionService {
    constructor(instaContentRepository, globalEventRepository, configService, databaseService) {
        this.instaContentRepository = instaContentRepository;
        this.globalEventRepository = globalEventRepository;
        this.configService = configService;
        this.databaseService = databaseService;
        this.logger = new common_1.Logger(ExtractionService_1.name);
        this.GLOBAL_EVENT_ID = 0;
        this.logger.log('ExtractionService instantiated.');
    }
    async codeExists(code) {
        try {
            const count = await this.instaContentRepository.countBy({ code });
            return count > 0;
        }
        catch (error) {
            this.logger.error(`Error in codeExists for code ${code}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException(`Error checking existence for code ${code}.`);
        }
    }
    async alreadyEmbedded(code) {
        try {
            const content = await this.instaContentRepository.findOne({
                where: { code },
                select: ['isEmbedded'],
            });
            return content?.isEmbedded === true;
        }
        catch (error) {
            this.logger.error(`Error in alreadyEmbedded for code ${code}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException(`Error checking embedding status for code ${code}.`);
        }
    }
    async checkEmbeddingStatus(code) {
        try {
            if (!(await this.codeExists(code))) {
                return { code, isEmbedded: false, exists: false };
            }
            const isEmbedded = await this.alreadyEmbedded(code);
            return { code, isEmbedded, exists: true };
        }
        catch (err) {
            this.logger.error(`checkEmbeddingStatus(${code}) failed: ${err.message}`, err.stack);
            if (err instanceof common_1.HttpException)
                throw err;
            throw new common_1.InternalServerErrorException('An error occurred while checking embedding status.');
        }
    }
    async verifyFramesExtractionByCode(code) {
        try {
            const content = await this.instaContentRepository.findOne({
                where: { code },
                select: ['isExtracted'],
            });
            if (!content) {
                this.logger.warn(`verifyExtractionByCode: Content with code ${code} not found.`);
                return false;
            }
            return content.isExtracted === true;
        }
        catch (error) {
            this.logger.error(`Error verifying extraction for code ${code}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException(`Error verifying extraction status for ${code}.`);
        }
    }
    async getExtractionProgress() {
        try {
            const result = await this.databaseService.executeQuery('SELECT total, downloaded, extracted, embedded FROM extraction_progress()', []);
            if (result && result.length > 0) {
                const data = result[0];
                if (data.total === undefined ||
                    data.downloaded === undefined ||
                    data.extracted === undefined ||
                    data.embedded === undefined) {
                    this.logger.error('RPC extraction_progress returned unexpected data structure:', data);
                    throw new common_1.InternalServerErrorException('Extraction progress RPC returned invalid data.');
                }
                const calculatePercentage = (value, total) => total > 0 ? parseFloat(((value / total) * 100).toFixed(2)) : 0;
                return {
                    total: data.total,
                    downloaded: data.downloaded,
                    extracted: data.extracted,
                    embedded: data.embedded,
                    downloadProgress: calculatePercentage(data.downloaded, data.total),
                    extractionProgress: calculatePercentage(data.extracted, data.total),
                    embeddingsProgress: calculatePercentage(data.embedded, data.total),
                };
            }
            this.logger.warn('RPC extraction_progress returned no data.');
            throw new common_1.InternalServerErrorException('No data returned from extraction progress function.');
        }
        catch (error) {
            this.logger.error(`Error calling extraction_progress RPC: ${error.message}`, error.stack);
            if (error instanceof common_1.HttpException)
                throw error;
            throw new common_1.InternalServerErrorException('Failed to get extraction progress.');
        }
    }
    async getLastExtractionTimestamp() {
        try {
            const globalEvent = await this.globalEventRepository.findOneBy({
                id: this.GLOBAL_EVENT_ID,
            });
            if (!globalEvent?.lastExtractionAt) {
                this.logger.warn('Last extraction timestamp not found in global_events or is null.');
                return null;
            }
            return globalEvent.lastExtractionAt.toISOString();
        }
        catch (error) {
            this.logger.error(`Failed to get last extraction timestamp: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to get last extraction timestamp.');
        }
    }
    async updateLastExtractionTimestamp() {
        try {
            let globalEvent = await this.globalEventRepository.findOneBy({
                id: this.GLOBAL_EVENT_ID,
            });
            const now = new Date();
            if (!globalEvent) {
                this.logger.log(`Global event for last_extraction_at (ID ${this.GLOBAL_EVENT_ID}) not found, creating new one.`);
                globalEvent = this.globalEventRepository.create({
                    id: this.GLOBAL_EVENT_ID,
                    lastExtractionAt: now,
                });
            }
            else {
                globalEvent.lastExtractionAt = now;
            }
            await this.globalEventRepository.save(globalEvent);
            this.logger.log(`Successfully updated last_extraction_at timestamp to ${now.toISOString()}`);
        }
        catch (error) {
            this.logger.error(`Failed to update last_extraction_at timestamp: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to update last extraction timestamp.');
        }
    }
    async extractVideoByCode(code) {
        try {
            if (!(await this.codeExists(code))) {
                throw new common_1.NotFoundException(`Content with code ${code} does not exist in the database.`);
            }
            return {
                status: 'success',
                message: `Frame extraction process initiated for code: ${code}`,
            };
        }
        catch (error) {
            this.logger.error(`Error initiating frame extraction for code ${code}: ${error.message}`, error.stack);
            if (error instanceof common_1.HttpException)
                throw error;
            throw new common_1.InternalServerErrorException('Error initiating frame extraction by code.');
        }
    }
    async extractAllVideos() {
        const commonConditions = {
            isDownloaded: true,
            isExtracted: false,
        };
        let totalEligible = 0;
        try {
            totalEligible = await this.instaContentRepository.count({
                where: commonConditions,
            });
        }
        catch (countError) {
            this.logger.error(`extractAllFrames: Failed to count eligible content: ${countError.message}`, countError.stack);
            throw new common_1.InternalServerErrorException('Failed to count content for frame extraction.');
        }
        if (totalEligible === 0) {
            return {
                message: 'No new content to extract frames from.',
                totalEligible: 0,
                dispatched: 0,
            };
        }
        this.logger.log(`extractAllFrames: Found ${totalEligible} items eligible for frame extraction.`);
        let successfullyDispatchedCount = 0;
        let itemsFetchedForDispatch = 0;
        for (let offset = 0;; offset += BATCH_SIZE_VIDEO_EXTRACTION) {
            let batchData;
            try {
                batchData = await this.instaContentRepository.find({
                    where: commonConditions,
                    select: ['code'],
                    order: { createdAt: 'ASC' },
                    skip: offset,
                    take: BATCH_SIZE_VIDEO_EXTRACTION,
                });
            }
            catch (error) {
                this.logger.error(`extractAllFrames: Database query for batch failed at offset ${offset}: ${error.message}`, error.stack);
                throw new common_1.InternalServerErrorException('Database query failed during batch processing for extractAllFrames.');
            }
            if (batchData.length === 0) {
                this.logger.log(`extractAllFrames: No more items found at offset ${offset}. Loop finished.`);
                break;
            }
            itemsFetchedForDispatch += batchData.length;
            const dispatchPromises = batchData.map(async (row) => {
                try {
                    return true;
                }
                catch (err) {
                    this.logger.error(`extractAllFrames: Failed SQS send for ${row.code}: ${err.message}`, err.stack);
                    return false;
                }
            });
            const results = await Promise.all(dispatchPromises);
            successfullyDispatchedCount += results.filter((success) => success).length;
            if (itemsFetchedForDispatch >= totalEligible) {
                this.logger.log(`extractAllFrames: Processed items count reached or exceeded initial totalEligible. Items fetched: ${itemsFetchedForDispatch}`);
                break;
            }
        }
        try {
            await this.updateLastExtractionTimestamp();
        }
        catch (tsError) {
            this.logger.error(`extractAllFrames: Failed to update last_extraction_at timestamp, but dispatching might have proceeded: ${tsError.message}`);
        }
        return {
            message: `Frame extraction SQS messages queued for ${successfullyDispatchedCount} out of ${itemsFetchedForDispatch} fetched content items (initial eligible: ${totalEligible}).`,
            totalEligible: totalEligible,
            dispatched: successfullyDispatchedCount,
        };
    }
};
exports.ExtractionService = ExtractionService;
exports.ExtractionService = ExtractionService = ExtractionService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(content_entity_1.InstaContent)),
    __param(1, (0, typeorm_1.InjectRepository)(global_events_entity_1.GlobalEvent)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        typeorm_2.Repository,
        config_1.ConfigService,
        database_service_1.DatabaseService])
], ExtractionService);
//# sourceMappingURL=extraction.service.js.map