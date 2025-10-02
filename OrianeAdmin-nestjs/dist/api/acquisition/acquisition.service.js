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
var AcquisitionService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AcquisitionService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const aws_module_1 = require("../../aws/aws.module");
const oriane_user_entity_1 = require("../../entities/oriane-user.entity");
const global_events_entity_1 = require("../../entities/global-events.entity");
const aws_sqs_service_1 = require("../../aws/aws.sqs.service");
let AcquisitionService = AcquisitionService_1 = class AcquisitionService {
    constructor(orianeUserRepository, globalEventRepository, awsSqsAcquisitionService, awsSqsContentService) {
        this.orianeUserRepository = orianeUserRepository;
        this.globalEventRepository = globalEventRepository;
        this.awsSqsAcquisitionService = awsSqsAcquisitionService;
        this.awsSqsContentService = awsSqsContentService;
        this.logger = new common_1.Logger(AcquisitionService_1.name);
        this.GLOBAL_EVENT_ID = 1;
    }
    async runAcquisition(debug = false, batchSize = 10) {
        const startTime = new Date();
        this.logger.log(`Starting acquisition run at ${startTime.toISOString()}`);
        if (debug)
            this.logger.debug('Debug mode enabled for acquisition run');
        const limit = 5000;
        let dispatchedUsernames = 0;
        let errorCount = 0;
        const today = new Date();
        today.setUTCHours(0, 0, 0, 0);
        if (debug)
            this.logger.debug(`Acquisition run: Cutoff date = ${today.toISOString()}`);
        const baseQueryConditions = (qb) => {
            qb.where('user.isWatched = :isWatched', { isWatched: true })
                .andWhere(new typeorm_2.Brackets((subQb) => {
                subQb
                    .where('user.isDeactivated = :isDeactivated', {
                    isDeactivated: false,
                })
                    .orWhere('user.isDeactivated IS NULL');
            }))
                .andWhere(new typeorm_2.Brackets((subQb) => {
                subQb
                    .where('user.stateError = :stateError', { stateError: false })
                    .orWhere('user.stateError IS NULL');
            }))
                .andWhere(new typeorm_2.Brackets((subQb) => {
                subQb
                    .where('user.lastFetched IS NULL')
                    .orWhere('user.lastFetched < :today', { today });
            }));
        };
        let totalUsers = 0;
        try {
            const countQueryBuilder = this.orianeUserRepository.createQueryBuilder('user');
            baseQueryConditions(countQueryBuilder);
            totalUsers = await countQueryBuilder.getCount();
            if (debug)
                this.logger.debug(`Acquisition run: Total users to process = ${totalUsers}`);
        }
        catch (countErr) {
            this.logger.error(`Acquisition run: Count failed: ${countErr.message}`, countErr.stack);
            throw new common_1.InternalServerErrorException('Failed to count watched users for acquisition.');
        }
        if (totalUsers === 0) {
            this.logger.log('Acquisition run: No users to process.');
            await this.updateLastAcquisitionTimestamp();
            return {
                total: 0,
                dispatched: 0,
                errors: 0,
                success: true,
                message: 'No users needed processing for this global acquisition run.',
            };
        }
        for (let offset = 0; offset < totalUsers; offset += limit) {
            if (debug)
                this.logger.debug(`Acquisition run: Fetching users offset=${offset}, limit=${limit}`);
            let usersToDispatch;
            try {
                const pageQueryBuilder = this.orianeUserRepository.createQueryBuilder('user');
                baseQueryConditions(pageQueryBuilder);
                usersToDispatch = await pageQueryBuilder
                    .select(['user.username'])
                    .orderBy('user.username', 'ASC')
                    .skip(offset)
                    .take(limit)
                    .getMany();
            }
            catch (fetchErr) {
                this.logger.error(`Acquisition run: Fetch failed at offset ${offset}: ${fetchErr.message}`, fetchErr.stack);
                errorCount += limit;
                continue;
            }
            if (!usersToDispatch?.length) {
                if (debug)
                    this.logger.debug(`Acquisition run: No users at offset ${offset}, done paging.`);
                break;
            }
            if (debug)
                this.logger.debug(`Acquisition run: Got ${usersToDispatch.length} users for this page.`);
            const messages = usersToDispatch
                .filter((user) => user.username)
                .map((user) => ({ username: user.username }));
            if (messages.length === 0) {
                if (debug)
                    this.logger.debug('No valid usernames in this batch');
                continue;
            }
            if (debug)
                this.logger.debug(`Acquisition run: Sending batch of ${messages.length} messages to SQS`);
            try {
                const batchResult = await this.awsSqsAcquisitionService.sendMessageBatch(messages, batchSize);
                dispatchedUsernames += batchResult.success;
                errorCount += batchResult.errors;
                if (debug) {
                    this.logger.debug(`Acquisition run: Batch sent - ${batchResult.success} successful, ${batchResult.errors} failed`);
                }
                if (batchResult.failedMessages.length > 0) {
                    this.logger.warn(`Acquisition run: ${batchResult.failedMessages.length} messages failed to send`);
                }
            }
            catch (sqsErr) {
                this.logger.error(`Acquisition run: Failed to send batch SQS messages: ${sqsErr.message || sqsErr}`, sqsErr.stack);
                errorCount += messages.length;
            }
        }
        await this.updateLastAcquisitionTimestamp();
        const endTime = new Date();
        const duration = endTime.getTime() - startTime.getTime();
        const success = totalUsers > 0 && dispatchedUsernames > 0;
        const resultMessage = success
            ? `Successfully dispatched ${dispatchedUsernames} out of ${totalUsers} users for content update. Duration: ${duration}ms`
            : `Dispatched ${dispatchedUsernames} out of ${totalUsers} users. Errors: ${errorCount}. Duration: ${duration}ms. Check logs.`;
        this.logger.log(`Acquisition run completed: ${resultMessage}`);
        return {
            total: totalUsers,
            dispatched: dispatchedUsernames,
            errors: errorCount,
            success,
            message: resultMessage,
        };
    }
    async runAcquisitionByUsername(username) {
        try {
            const user = await this.orianeUserRepository.findOneBy({ username });
            if (!user) {
                throw new common_1.NotFoundException(`User not found: ${username}`);
            }
            const messagePayload = { username };
            this.logger.log(`Sending SQS message for user ${username}:`, JSON.stringify(messagePayload, null, 2));
            await this.awsSqsAcquisitionService.sendMessage(messagePayload);
            this.logger.log(`Content update SQS message successfully sent for user ${username}`);
            return {
                success: true,
                message: `Content update triggered for ${username}`,
            };
        }
        catch (error) {
            this.logger.error(`Error running acquisition for user ${username}: ${error.message}`, error.stack);
            if (error instanceof common_1.HttpException)
                throw error;
            throw new common_1.InternalServerErrorException(`Failed to run acquisition for ${username}`);
        }
    }
    async getAcquisitionProgress() {
        const todayStart = new Date();
        todayStart.setUTCHours(0, 0, 0, 0);
        const baseConditions = (qb) => {
            qb.where('user.isWatched = :isWatched', { isWatched: true })
                .andWhere(new typeorm_2.Brackets((subQb) => {
                subQb
                    .where('user.isDeactivated = :isDeactivated', {
                    isDeactivated: false,
                })
                    .orWhere('user.isDeactivated IS NULL');
            }))
                .andWhere(new typeorm_2.Brackets((subQb) => {
                subQb
                    .where('user.stateError = :stateError', { stateError: false })
                    .orWhere('user.stateError IS NULL');
            }));
        };
        try {
            const totalQuery = this.orianeUserRepository.createQueryBuilder('user');
            baseConditions(totalQuery);
            const total = await totalQuery.getCount();
            const fetchedTodayQuery = this.orianeUserRepository.createQueryBuilder('user');
            baseConditions(fetchedTodayQuery);
            fetchedTodayQuery.andWhere('user.lastFetched >= :todayStart', {
                todayStart,
            });
            const fetchedToday = await fetchedTodayQuery.getCount();
            const progress = total > 0 ? parseFloat(((fetchedToday / total) * 100).toFixed(2)) : 0;
            return { total, fetched: fetchedToday, progress };
        }
        catch (error) {
            this.logger.error(`Error fetching acquisition progress: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to fetch acquisition progress.');
        }
    }
    async getLastAcquisitionTimestamp() {
        try {
            const globalEvent = await this.globalEventRepository.findOneBy({
                id: this.GLOBAL_EVENT_ID,
            });
            if (!globalEvent?.lastAcquisitionAt) {
                this.logger.warn('Last acquisition timestamp not found in global_events or is null.');
                return null;
            }
            return globalEvent.lastAcquisitionAt.toISOString();
        }
        catch (error) {
            this.logger.error(`Failed to get last acquisition timestamp: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to get last acquisition timestamp.');
        }
    }
    async updateLastAcquisitionTimestamp() {
        try {
            let globalEvent = await this.globalEventRepository.findOneBy({
                id: this.GLOBAL_EVENT_ID,
            });
            const now = new Date();
            if (!globalEvent) {
                this.logger.log(`Global event for last_acquisition_at (ID ${this.GLOBAL_EVENT_ID}) not found, creating new one.`);
                globalEvent = this.globalEventRepository.create({
                    id: this.GLOBAL_EVENT_ID,
                    lastAcquisitionAt: now,
                    lastProfileCollectorAt: now,
                    lastExtractionAt: now,
                });
            }
            else {
                globalEvent.lastAcquisitionAt = now;
            }
            await this.globalEventRepository.save(globalEvent);
            this.logger.log(`Successfully updated last_acquisition_at timestamp to ${now.toISOString()}`);
        }
        catch (error) {
            this.logger.error(`Failed to update last_acquisition_at timestamp: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to update last global acquisition timestamp.');
        }
    }
    createContentUpdateMessage(username) {
        return {
            username: username,
            timestamp: new Date().toISOString(),
            source: 'acquisition-service',
            action: 'content-update',
        };
    }
    getMessageFormat() {
        return {
            description: 'SQS message format for content updates',
            example: this.createContentUpdateMessage('example_username'),
            fields: {
                username: 'string - Instagram username to process',
                timestamp: 'string - ISO timestamp when message was created',
                source: 'string - Service that created the message',
                action: 'string - Type of action to perform',
            },
        };
    }
    async runVideoContentUpdate(videoCode) {
        try {
            const messagePayload = { code: videoCode };
            this.logger.log(`Sending SQS message for video code ${videoCode}:`, JSON.stringify(messagePayload, null, 2));
            await this.awsSqsContentService.sendMessage(messagePayload);
            this.logger.log(`Video content update SQS message successfully sent for code ${videoCode}`);
            return {
                success: true,
                message: `Video content update triggered for code ${videoCode}`,
            };
        }
        catch (error) {
            this.logger.error(`Error running video content update for code ${videoCode}: ${error.message}`, error.stack);
            if (error instanceof common_1.HttpException)
                throw error;
            throw new common_1.InternalServerErrorException(`Failed to run video content update for ${videoCode}`);
        }
    }
    async runAcquisitionFast(debug = false, batchSize = 10) {
        const startTime = new Date();
        this.logger.log(`Starting FAST acquisition run at ${startTime.toISOString()}`);
        if (debug)
            this.logger.debug('Debug mode enabled for fast acquisition run');
        const today = new Date();
        today.setUTCHours(0, 0, 0, 0);
        if (debug)
            this.logger.debug(`Fast acquisition run: Cutoff date = ${today.toISOString()}`);
        const baseQueryConditions = (qb) => {
            qb.where('user.isWatched = :isWatched', { isWatched: true })
                .andWhere(new typeorm_2.Brackets((subQb) => {
                subQb
                    .where('user.isDeactivated = :isDeactivated', {
                    isDeactivated: false,
                })
                    .orWhere('user.isDeactivated IS NULL');
            }))
                .andWhere(new typeorm_2.Brackets((subQb) => {
                subQb
                    .where('user.stateError = :stateError', { stateError: false })
                    .orWhere('user.stateError IS NULL');
            }))
                .andWhere(new typeorm_2.Brackets((subQb) => {
                subQb
                    .where('user.lastFetched IS NULL')
                    .orWhere('user.lastFetched < :today', { today });
            }));
        };
        let totalUsers = 0;
        let allUsernames = [];
        try {
            const queryBuilder = this.orianeUserRepository.createQueryBuilder('user');
            baseQueryConditions(queryBuilder);
            const users = await queryBuilder
                .select(['user.username'])
                .orderBy('user.username', 'ASC')
                .getMany();
            allUsernames = users
                .filter((user) => user.username)
                .map((user) => user.username);
            totalUsers = allUsernames.length;
            if (debug)
                this.logger.debug(`Fast acquisition run: Total users to process = ${totalUsers}`);
        }
        catch (fetchErr) {
            this.logger.error(`Fast acquisition run: Fetch failed: ${fetchErr.message}`, fetchErr.stack);
            throw new common_1.InternalServerErrorException('Failed to fetch watched users for fast acquisition.');
        }
        if (totalUsers === 0) {
            this.logger.log('Fast acquisition run: No users to process.');
            await this.updateLastAcquisitionTimestamp();
            return {
                total: 0,
                dispatched: 0,
                errors: 0,
                success: true,
                message: 'No users needed processing for this fast acquisition run.',
            };
        }
        const messages = allUsernames.map((username) => ({ username }));
        if (debug)
            this.logger.debug(`Fast acquisition run: Sending ${messages.length} messages in batches of ${batchSize}`);
        let dispatchedUsernames = 0;
        let errorCount = 0;
        try {
            const batchResult = await this.awsSqsAcquisitionService.sendMessageBatch(messages, batchSize);
            dispatchedUsernames = batchResult.success;
            errorCount = batchResult.errors;
            if (debug) {
                this.logger.debug(`Fast acquisition run: Batch send completed - ${batchResult.success} successful, ${batchResult.errors} failed`);
            }
            if (batchResult.failedMessages.length > 0) {
                this.logger.warn(`Fast acquisition run: ${batchResult.failedMessages.length} messages failed to send`);
            }
        }
        catch (sqsErr) {
            this.logger.error(`Fast acquisition run: Failed to send batch SQS messages: ${sqsErr.message || sqsErr}`, sqsErr.stack);
            errorCount = messages.length;
        }
        await this.updateLastAcquisitionTimestamp();
        const endTime = new Date();
        const duration = endTime.getTime() - startTime.getTime();
        const success = totalUsers > 0 && dispatchedUsernames > 0;
        const resultMessage = success
            ? `FAST: Successfully dispatched ${dispatchedUsernames} out of ${totalUsers} users for content update. Duration: ${duration}ms`
            : `FAST: Dispatched ${dispatchedUsernames} out of ${totalUsers} users. Errors: ${errorCount}. Duration: ${duration}ms. Check logs.`;
        this.logger.log(`Fast acquisition run completed: ${resultMessage}`);
        return {
            total: totalUsers,
            dispatched: dispatchedUsernames,
            errors: errorCount,
            success,
            message: resultMessage,
        };
    }
};
exports.AcquisitionService = AcquisitionService;
exports.AcquisitionService = AcquisitionService = AcquisitionService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(oriane_user_entity_1.OrianeUser)),
    __param(1, (0, typeorm_1.InjectRepository)(global_events_entity_1.GlobalEvent)),
    __param(2, (0, common_1.Inject)(aws_module_1.SQS_CONTENT_SERVICE)),
    __param(3, (0, common_1.Inject)(aws_module_1.SQS_INSTAGRAM_CONTENT_SERVICE)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        typeorm_2.Repository,
        aws_sqs_service_1.AwsSqsService,
        aws_sqs_service_1.AwsSqsService])
], AcquisitionService);
//# sourceMappingURL=acquisition.service.js.map