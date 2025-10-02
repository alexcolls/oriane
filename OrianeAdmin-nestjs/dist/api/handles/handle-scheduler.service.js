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
var HandleSchedulerService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.HandleSchedulerService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const oriane_user_entity_1 = require("../../entities/oriane-user.entity");
const profile_collector_service_1 = require("../users/instagram/profile-collector.service");
const HANDLE_PROCESSING_BATCH_SIZE = 500;
const HANDLE_PROCESSING_CONCURRENT_LIMIT = 10;
const HANDLE_PROCESSING_DELAY_MS = 500;
let HandleSchedulerService = HandleSchedulerService_1 = class HandleSchedulerService {
    constructor(orianeUserRepository, profileCollectorService) {
        this.orianeUserRepository = orianeUserRepository;
        this.profileCollectorService = profileCollectorService;
        this.logger = new common_1.Logger(HandleSchedulerService_1.name);
        this.logger.log('HandleSchedulerService instantiated.');
    }
    getNextMonthStart() {
        const now = new Date();
        return new Date(now.getFullYear(), now.getMonth() + 1, 1);
    }
    async reRunSchedule() {
        this.logger.log('🔄 Running scheduled task: Processing unverified/error OrianeUsers');
        let offset = 0;
        let continueFetching = true;
        while (continueFetching) {
            let usersBatch;
            try {
                usersBatch = await this.orianeUserRepository.find({
                    where: {
                        accountStatus: (0, typeorm_2.Not)('Checked'),
                        isDeactivated: false,
                    },
                    order: { priority: 'DESC', nextCheckAt: 'ASC' },
                    skip: offset,
                    take: HANDLE_PROCESSING_BATCH_SIZE,
                });
            }
            catch (error) {
                this.logger.error(`❌ Failed to fetch users for reRunSchedule (offset ${offset}): ${error.message}`, error.stack);
                throw new common_1.InternalServerErrorException('Failed to fetch users batch for re-run.');
            }
            if (!usersBatch || usersBatch.length === 0) {
                this.logger.log('✅ No more users to process in reRunSchedule.');
                continueFetching = false;
                break;
            }
            this.logger.log(`reRunSchedule: Processing batch of ${usersBatch.length} users (offset ${offset})...`);
            for (let i = 0; i < usersBatch.length; i += HANDLE_PROCESSING_CONCURRENT_LIMIT) {
                const concurrentBatch = usersBatch.slice(i, i + HANDLE_PROCESSING_CONCURRENT_LIMIT);
                const processingPromises = concurrentBatch.map(async (user) => {
                    try {
                        const result = await this.processSingleUser(user.username);
                        this.logger.log(`✅ Processed (reRun) ${user.username}: ${result.message}`);
                    }
                    catch (error) {
                        this.logger.error(`❌ Error processing (reRun) ${user.username}: ${error.message}`, error.stack);
                    }
                });
                await Promise.allSettled(processingPromises);
                if (HANDLE_PROCESSING_DELAY_MS > 0) {
                    await new Promise((resolve) => setTimeout(resolve, HANDLE_PROCESSING_DELAY_MS));
                }
            }
            offset += HANDLE_PROCESSING_BATCH_SIZE;
        }
        this.logger.log('✅ Finished reRunSchedule processing all pending users.');
    }
    async scheduleHandles() {
        this.logger.log('🔄 Running scheduled task: Processing OrianeUsers due for check');
        const now = new Date();
        let offset = 0;
        let continueFetching = true;
        while (continueFetching) {
            let handlesBatch;
            try {
                handlesBatch = await this.orianeUserRepository.find({
                    where: {
                        nextCheckAt: (0, typeorm_2.LessThanOrEqual)(now),
                        isDeactivated: false,
                    },
                    order: { priority: 'DESC', nextCheckAt: 'ASC' },
                    skip: offset,
                    take: HANDLE_PROCESSING_BATCH_SIZE,
                });
            }
            catch (error) {
                this.logger.error(`Failed to fetch handles for schedule (offset ${offset}): ${error.message}`, error.stack);
                throw new common_1.InternalServerErrorException('Failed to fetch handles batch for schedule.');
            }
            if (!handlesBatch || handlesBatch.length === 0) {
                this.logger.log('✅ No more handles to process in scheduleHandles.');
                continueFetching = false;
                break;
            }
            this.logger.log(`scheduleHandles: Processing batch of ${handlesBatch.length} handles (offset ${offset})...`);
            for (let i = 0; i < handlesBatch.length; i += HANDLE_PROCESSING_CONCURRENT_LIMIT) {
                const concurrentBatch = handlesBatch.slice(i, i + HANDLE_PROCESSING_CONCURRENT_LIMIT);
                const processingPromises = concurrentBatch.map(async (handle) => {
                    try {
                        const result = await this.processSingleUser(handle.username);
                        this.logger.log(`✅ Processed (scheduled) ${handle.username}: ${result.message}`);
                    }
                    catch (error) {
                        this.logger.error(`❌ Error processing (scheduled) ${handle.username}: ${error.message}`, error.stack);
                    }
                });
                await Promise.allSettled(processingPromises);
                if (HANDLE_PROCESSING_DELAY_MS > 0) {
                    await new Promise((resolve) => setTimeout(resolve, HANDLE_PROCESSING_DELAY_MS));
                }
            }
            offset += HANDLE_PROCESSING_BATCH_SIZE;
        }
        this.logger.log('✅ Finished scheduleHandles processing.');
    }
    handleCron() {
        this.logger.log('Cron triggered: Executing scheduleHandles()');
        this.scheduleHandles().catch((error) => {
            this.logger.error(`Unhandled error during cron execution of scheduleHandles: ${error.message}`, error.stack);
        });
    }
    async processSingleUser(username) {
        const user = await this.orianeUserRepository.findOneBy({ username });
        if (!user) {
            this.logger.warn(`User with username ${username} not found during processSingleUser.`);
            throw new common_1.NotFoundException(`User with username ${username} not found.`);
        }
        const updatePayload = {};
        try {
            const profile = await this.profileCollectorService.collectProfile(user.username);
            if (!profile) {
                updatePayload.accountStatus = 'Error';
                updatePayload.stateError = true;
                updatePayload.errorMessage = `Profile for ${username} not found on external platform.`;
                await this.orianeUserRepository.update({ id: user.id }, updatePayload);
                this.logger.warn(updatePayload.errorMessage);
                return { success: false, message: updatePayload.errorMessage };
            }
            updatePayload.lastChecked = new Date();
            updatePayload.nextCheckAt = this.getNextMonthStart();
            updatePayload.accountStatus = 'Checked';
            updatePayload.stateError = false;
            updatePayload.errorMessage = null;
            await this.orianeUserRepository.update({ id: user.id }, updatePayload);
            return {
                success: true,
                message: `Profile for ${username} successfully scraped and user status updated.`,
            };
        }
        catch (err) {
            this.logger.error(`Error processing profile for ${username}: ${err.message}`, err.stack);
            updatePayload.accountStatus = 'Error';
            updatePayload.stateError = true;
            updatePayload.errorMessage = err.message.substring(0, 2048);
            try {
                await this.orianeUserRepository.update({ id: user.id }, updatePayload);
            }
            catch (dbUpdateError) {
                this.logger.error(`Failed to update error state for user ${username} after processing error: ${dbUpdateError.message}`, dbUpdateError.stack);
            }
            throw new common_1.InternalServerErrorException(`Error processing ${username}: ${err.message}`);
        }
    }
    async refreshAllHandles(batchSize = HANDLE_PROCESSING_BATCH_SIZE, concurrentLimit = HANDLE_PROCESSING_CONCURRENT_LIMIT, delayMs = HANDLE_PROCESSING_DELAY_MS) {
        this.logger.log('🔄 Running task: Refresh all non-deactivated handles');
        let offset = 0;
        let continueFetching = true;
        while (continueFetching) {
            let handlesBatch;
            try {
                handlesBatch = await this.orianeUserRepository.find({
                    select: ['username', 'id', 'environment'],
                    where: { isDeactivated: false },
                    order: { username: 'ASC' },
                    skip: offset,
                    take: batchSize,
                });
            }
            catch (error) {
                this.logger.error(`Failed to fetch handles for refreshAll (offset ${offset}): ${error.message}`, error.stack);
                throw new common_1.InternalServerErrorException('Failed to fetch handles batch for refresh.');
            }
            if (!handlesBatch || handlesBatch.length === 0) {
                this.logger.log('✅ No more handles to process in refreshAllHandles.');
                continueFetching = false;
                break;
            }
            this.logger.log(`refreshAllHandles: Processing batch of ${handlesBatch.length} handles (offset ${offset})...`);
            for (let i = 0; i < handlesBatch.length; i += concurrentLimit) {
                const concurrentBatch = handlesBatch.slice(i, i + concurrentLimit);
                const processingPromises = concurrentBatch.map(async (handle) => {
                    try {
                        const result = await this.processSingleUser(handle.username);
                        this.logger.log(`✅ Processed (refreshAll) ${handle.username}: ${result.message}`);
                    }
                    catch (error) {
                        this.logger.error(`❌ Error processing (refreshAll) ${handle.username}: ${error.message}`, error.stack);
                    }
                });
                await Promise.allSettled(processingPromises);
                if (delayMs > 0) {
                    await new Promise((resolve) => setTimeout(resolve, delayMs));
                }
            }
            offset += batchSize;
        }
        this.logger.log('✅ Finished refreshAllHandles processing.');
    }
    async refreshAllHandlesProgress() {
        const todayStart = new Date();
        todayStart.setHours(0, 0, 0, 0);
        const commonConditions = {
            isDeactivated: false,
        };
        try {
            const total = await this.orianeUserRepository.count({
                where: commonConditions,
            });
            const checked_today = await this.orianeUserRepository.count({
                where: {
                    ...commonConditions,
                    lastChecked: (0, typeorm_2.MoreThanOrEqual)(todayStart),
                },
            });
            const progress = total > 0 ? parseFloat(((checked_today / total) * 100).toFixed(2)) : 0;
            return { total, checked_today: checked_today, progress };
        }
        catch (error) {
            this.logger.error(`Error fetching refreshAllHandles progress: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to fetch refreshAllHandles progress.');
        }
    }
};
exports.HandleSchedulerService = HandleSchedulerService;
exports.HandleSchedulerService = HandleSchedulerService = HandleSchedulerService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(oriane_user_entity_1.OrianeUser)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        profile_collector_service_1.ProfileCollectorService])
], HandleSchedulerService);
//# sourceMappingURL=handle-scheduler.service.js.map