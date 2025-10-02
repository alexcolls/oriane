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
var AiJobsService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AiJobsService = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const aws_sqs_service_1 = require("../../../aws/aws.sqs.service");
const utils_1 = require("../../../aws/utils");
const models_1 = require("../../../models/models");
const utils_2 = require("../../../utils");
const aws_module_1 = require("../../../aws/aws.module");
const ai_jobs_entity_1 = require("../../../entities/ai-jobs.entity");
const ai_jobs_run_entity_1 = require("../../../entities/ai-jobs-run.entity");
const content_entity_1 = require("../../../entities/content.entity");
const ai_errors_entity_1 = require("../../../entities/ai-errors.entity");
const AI_JOB_RUN_SQS_BATCH_SIZE = 1000;
const AI_JOB_RUN_DB_PAGE_LIMIT = 1000;
const SQS_RETRY_COUNT = 5;
const SQS_RETRY_DELAY = 5000;
let AiJobsService = AiJobsService_1 = class AiJobsService {
    constructor(aiJobRepository, aiJobsRunRepository, instaContentRepository, aiErrorRepository, configService, awsSqsService) {
        this.aiJobRepository = aiJobRepository;
        this.aiJobsRunRepository = aiJobsRunRepository;
        this.instaContentRepository = instaContentRepository;
        this.aiErrorRepository = aiErrorRepository;
        this.configService = configService;
        this.awsSqsService = awsSqsService;
        this.logger = new common_1.Logger(AiJobsService_1.name);
        this.debug = this.configService.get('DEBUG') ?? false;
        this.logger.log('AiJobsService (Direct Translation) instantiated.');
    }
    async internalCreateNewAiJob(dto) {
        const { monitoredVideo, model, useGpu, threshold } = dto;
        if (!models_1.MODELS?.includes(model.toUpperCase())) {
            throw new common_1.BadRequestException(`Invalid model: ${model}`);
        }
        const existingJob = await this.aiJobRepository.findOne({
            where: { monitoredVideo, model, useGpu: useGpu ?? false },
        });
        if (existingJob) {
            throw new common_1.ConflictException(`Duplicate job: An AiJob already exists for video ${monitoredVideo} with model ${model} and use_gpu ${useGpu ?? false}`);
        }
        const content = await this.instaContentRepository.findOne({
            where: { code: monitoredVideo },
            select: ['publishDate'],
        });
        if (!content?.publishDate) {
            throw new common_1.NotFoundException(`InstaContent with code ${monitoredVideo} not found or has no publish date.`);
        }
        const newJobPayload = {
            monitoredVideo,
            model,
            useGpu: useGpu ?? false,
            publishedDate: content.publishDate,
            threshold: threshold ?? 0.5,
        };
        const aiJob = this.aiJobRepository.create(newJobPayload);
        return this.aiJobRepository.save(aiJob);
    }
    async startJobWorkflow(dto) {
        const aiJobEntity = await this.internalCreateNewAiJob(dto);
        const aiJobRunEntity = await this.executeJobRunLogic(aiJobEntity.id);
        const { runs: _jobRuns, ...jobDetails } = aiJobEntity;
        const { aiJob: _runAiJob, ...runDetails } = aiJobRunEntity;
        return {
            aiJob: jobDetails,
            aiJobRun: runDetails,
        };
    }
    async executeJobRunLogic(jobId) {
        if (!/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(jobId)) {
            throw new common_1.BadRequestException(`Invalid UUID for jobId: ${jobId}`);
        }
        const aiJob = await this.aiJobRepository.findOneBy({ id: jobId });
        if (!aiJob) {
            throw new common_1.NotFoundException(`AiJob with ID ${jobId} not found.`);
        }
        const lastAiJobRun = await this.getLastAiJobRunForJob(jobId);
        let comparisonsToProcess = 0;
        let dateToCompareFrom = aiJob.publishedDate;
        if (lastAiJobRun) {
            this.logger.debug(`Last run found (ID: ${lastAiJobRun.id}). Determining new videos since ${lastAiJobRun.lastPublishedDate || aiJob.publishedDate}.`);
            dateToCompareFrom = lastAiJobRun.lastPublishedDate || aiJob.publishedDate;
            const watchedVideosStats = await this.getWatchedVideosStatsByDate(dateToCompareFrom);
            comparisonsToProcess = watchedVideosStats.watchedVideosAfter;
        }
        else {
            const watchedVideosStats = await this.getWatchedVideosStatsByDate(aiJob.publishedDate);
            comparisonsToProcess = watchedVideosStats.watchedVideosAfter;
        }
        if (comparisonsToProcess === 0) {
            this.logger.log(`No new videos to process for job ${jobId} since ${dateToCompareFrom.toISOString()}.`);
            const noNewContentRunData = {
                jobId: jobId,
                aiJob: aiJob,
                comparisonsToProcess: 0,
                comparisonsProcessed: 0,
                state: 'COMPLETED_NO_NEW_CONTENT',
                startedAt: new Date(),
                finishedAt: new Date(),
                lastPublishedDate: dateToCompareFrom,
            };
            const runRecord = this.aiJobsRunRepository.create(noNewContentRunData);
            return this.aiJobsRunRepository.save(runRecord);
        }
        const newRunData = {
            jobId: jobId,
            aiJob: aiJob,
            comparisonsToProcess: comparisonsToProcess,
            state: 'STARTING',
            estimatedCost: (0, utils_1.getSscdLambdaExpCost)(comparisonsToProcess),
            startedAt: new Date(),
        };
        let currentRun = this.aiJobsRunRepository.create(newRunData);
        currentRun = await this.aiJobsRunRepository.save(currentRun);
        this.logger.log(`Created AiJobsRun ${currentRun.id} for AiJob ${jobId} with state STARTING.`);
        try {
            const dispatchResult = await this.processAndDispatchRunBatches(currentRun, aiJob, dateToCompareFrom);
            currentRun.comparisonsProcessed = dispatchResult.dispatchedCount;
            currentRun.comparisonsFailed =
                dispatchResult.totalVideosFoundInRun - dispatchResult.dispatchedCount;
            currentRun.lastVideoCode = dispatchResult.lastProcessedCode;
            currentRun.lastPublishedDate = dispatchResult.lastProcessedDate;
            currentRun.finishedAt = new Date();
            if (dispatchResult.dispatchedCount ===
                dispatchResult.totalVideosFoundInRun &&
                dispatchResult.totalVideosFoundInRun > 0) {
                currentRun.state = 'COMPLETED_DISPATCH';
            }
            else if (dispatchResult.totalVideosFoundInRun > 0) {
                currentRun.state = 'PARTIAL_DISPATCH_ERROR';
            }
            else if (comparisonsToProcess > 0 &&
                dispatchResult.totalVideosFoundInRun === 0) {
                currentRun.state = 'ERROR_NO_VIDEOS_FOUND_UNEXPECTEDLY';
            }
            else {
                currentRun.state = 'COMPLETED_NO_VIDEOS_PROCESSED';
            }
        }
        catch (processingError) {
            this.logger.error(`Error during SQS dispatch for run ${currentRun.id}: ${processingError.message}`, processingError.stack);
            currentRun.state = 'FAILED';
            currentRun.finishedAt = new Date();
            await this.recordErrorForRun(currentRun.id, jobId, 'PROCESS_AND_DISPATCH_EXCEPTION', processingError.message);
        }
        return this.aiJobsRunRepository.save(currentRun);
    }
    async processAndDispatchRunBatches(currentRun, aiJob, thresholdDate) {
        let dispatchedCount = 0;
        let totalVideosFoundInRun = 0;
        let latestDateProcessedInThisRun = thresholdDate;
        let latestCodeProcessedInThisRun = null;
        this.logger.debug(`Run ${currentRun.id}: Starting video fetch from ${thresholdDate.toISOString()} for job ${aiJob.id}`);
        let sqsBatch = [];
        for await (const page of this.fetchInstaContentForRun(thresholdDate)) {
            const { codes: videoCodesInPage, lastPublishDateInPage } = page;
            if (videoCodesInPage.length === 0)
                continue;
            totalVideosFoundInRun += videoCodesInPage.length;
            if (lastPublishDateInPage &&
                (!latestDateProcessedInThisRun ||
                    lastPublishDateInPage > latestDateProcessedInThisRun)) {
                latestDateProcessedInThisRun = lastPublishDateInPage;
            }
            for (const code of videoCodesInPage) {
                sqsBatch.push(code);
                if (sqsBatch.length >= AI_JOB_RUN_SQS_BATCH_SIZE) {
                    await this.dispatchSqsBatch(sqsBatch, aiJob, currentRun);
                    dispatchedCount += sqsBatch.length;
                    latestCodeProcessedInThisRun = code;
                    currentRun.comparisonsProcessed = dispatchedCount;
                    currentRun.lastVideoCode = latestCodeProcessedInThisRun;
                    currentRun.lastPublishedDate = latestDateProcessedInThisRun;
                    currentRun.state = 'PROCESSING_DISPATCH';
                    await this.aiJobsRunRepository.save(currentRun);
                    sqsBatch = [];
                }
            }
        }
        if (sqsBatch.length > 0) {
            await this.dispatchSqsBatch(sqsBatch, aiJob, currentRun);
            dispatchedCount += sqsBatch.length;
            latestCodeProcessedInThisRun = sqsBatch[sqsBatch.length - 1];
        }
        this.logger.log(`Run ${currentRun.id}: Found ${totalVideosFoundInRun} videos in total, dispatched ${dispatchedCount} videos.`);
        return {
            totalVideosFoundInRun,
            dispatchedCount,
            lastProcessedDate: latestDateProcessedInThisRun,
            lastProcessedCode: latestCodeProcessedInThisRun,
        };
    }
    async *fetchInstaContentForRun(thresholdDate) {
        let offset = 0;
        const safeThresholdDate = thresholdDate instanceof Date ? thresholdDate : new Date(thresholdDate);
        while (true) {
            try {
                const items = await this.instaContentRepository.find({
                    select: ['code', 'publishDate'],
                    where: {
                        isWatched: true,
                        publishDate: (0, typeorm_2.MoreThanOrEqual)(safeThresholdDate),
                        isExtracted: true,
                    },
                    order: { publishDate: 'ASC' },
                    skip: offset,
                    take: AI_JOB_RUN_DB_PAGE_LIMIT,
                });
                if (!items || items.length === 0)
                    break;
                const codes = items.map((item) => item.code);
                const lastPublishDateInPage = items.length > 0 ? items[items.length - 1].publishDate : null;
                yield { codes, lastPublishDateInPage };
                if (items.length < AI_JOB_RUN_DB_PAGE_LIMIT)
                    break;
                offset += AI_JOB_RUN_DB_PAGE_LIMIT;
            }
            catch (error) {
                this.logger.error(`Error in fetchInstaContentForRun: ${error.message}`, error.stack);
                throw new common_1.InternalServerErrorException(`Error in fetchInstaContentForRun: ${error.message}`);
            }
        }
    }
    async dispatchSqsBatch(batch, job, currentRun) {
        const messagePayload = this.buildSqsPayload(job.id, currentRun.id, job.monitoredVideo, batch, job.model);
        let attempt = 0;
        while (attempt < SQS_RETRY_COUNT) {
            try {
                await this.awsSqsService.sendMessage(messagePayload);
                if (this.debug) {
                    this.logger.debug(`SQS Batch of ${batch.length} dispatched for job ${job.id}, run ${currentRun.id}`);
                }
                return;
            }
            catch (error) {
                attempt++;
                this.logger.error(`Attempt ${attempt} to dispatch SQS batch for job ${job.id}, run ${currentRun.id} failed: ${error.message}`);
                if (attempt < SQS_RETRY_COUNT) {
                    await (0, utils_2.sleep)(SQS_RETRY_DELAY);
                }
                else {
                    const errMsg = `Failed to dispatch SQS batch for job ${job.id}, run ${currentRun.id} after ${SQS_RETRY_COUNT} attempts: ${error.message}`;
                    await this.recordErrorForRun(currentRun.id, job.id, batch.join(','), errMsg);
                    throw new common_1.InternalServerErrorException(errMsg);
                }
            }
        }
    }
    buildSqsPayload(jobId, runId, monitoredShortcode, batchCodes, model) {
        return {
            job_id: jobId,
            job_run_id: runId,
            monitored_shortcode: monitoredShortcode,
            watched_shortcodes: [...batchCodes],
            model: model.toLowerCase(),
            frame_details: true,
            platform: 'instagram',
            extension: 'jpg',
        };
    }
    async recordErrorForRun(runId, jobId, watchedVideoCodes, errorMessageText) {
        try {
            const errorToSave = {
                jobRunId: runId,
                jobId,
                watchedVideo: watchedVideoCodes,
                errorMessage: errorMessageText,
            };
            const errorRecord = this.aiErrorRepository.create(errorToSave);
            await this.aiErrorRepository.save(errorRecord);
        }
        catch (dbError) {
            this.logger.error(`Failed to record error in ai_errors for run ${runId}, job ${jobId}: ${dbError.message}`, dbError.stack);
        }
    }
    async getAiJobs(queryDto) {
        const { offset = 0, limit = 10, search } = queryDto;
        const qb = this.aiJobRepository.createQueryBuilder('ai_job');
        if (search) {
            qb.where('ai_job.monitoredVideo ILIKE :search OR ai_job.model ILIKE :search', { search: `%${search}%` });
        }
        try {
            const [data, total] = await qb
                .orderBy('ai_job.createdAt', 'DESC')
                .skip(offset)
                .take(limit)
                .getManyAndCount();
            const responseData = data.map((job) => {
                const { runs: _runs, ...jobDetails } = job;
                return jobDetails;
            });
            return { data: responseData, total };
        }
        catch (error) {
            this.logger.error(`Error fetching AI jobs: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve AI jobs.');
        }
    }
    async verifyAiJobExists(monitoredVideo, model, useGpu) {
        const count = await this.aiJobRepository.count({
            where: { monitoredVideo, model, useGpu },
        });
        return count > 0;
    }
    async getAiJobDetails(id) {
        const job = await this.aiJobRepository.findOneBy({ id });
        if (!job)
            throw new common_1.NotFoundException(`AiJob with ID ${id} not found`);
        const { runs: _runs, ...jobDetails } = job;
        return jobDetails;
    }
    async getAiJobsByMonitoredVideoCode(code) {
        const jobs = await this.aiJobRepository.find({
            where: { monitoredVideo: code },
        });
        return jobs.map((job) => {
            const { runs: _runs, ...jobDetails } = job;
            return jobDetails;
        });
    }
    async updateAiJobDefinition(id, dto) {
        const job = await this.aiJobRepository.preload({ id, ...dto });
        if (!job)
            throw new common_1.NotFoundException(`AiJob with ID ${id} not found for update.`);
        try {
            const savedJob = await this.aiJobRepository.save(job);
            const { runs: _runs, ...jobDetails } = savedJob;
            return jobDetails;
        }
        catch (error) {
            this.logger.error(`Error updating AiJob definition ${id}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to update AiJob definition.');
        }
    }
    async patchAiJobDefinition(id, dto) {
        const job = await this.aiJobRepository.findOneBy({ id });
        if (!job)
            throw new common_1.NotFoundException(`AiJob with ID ${id} not found for patch.`);
        this.aiJobRepository.merge(job, dto);
        try {
            const savedJob = await this.aiJobRepository.save(job);
            const { runs: _runs, ...jobDetails } = savedJob;
            return jobDetails;
        }
        catch (error) {
            this.logger.error(`Error patching AiJob definition ${id}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to patch AiJob definition.');
        }
    }
    async deleteAiJob(id) {
        const result = await this.aiJobRepository.delete(id);
        if (result.affected === 0)
            throw new common_1.NotFoundException(`AiJob with ID ${id} not found for deletion.`);
    }
    async getLastAiJobRunForJob(jobId) {
        return this.aiJobsRunRepository.findOne({
            where: { jobId },
            order: { createdAt: 'DESC' },
        });
    }
    async getAllRunsForJob(jobId, queryDto) {
        await this.getAiJobDetails(jobId);
        const { offset = 0, limit = 10 } = queryDto;
        const [data, totalInJob] = await this.aiJobsRunRepository.findAndCount({
            where: { jobId },
            order: { createdAt: 'DESC' },
            skip: offset,
            take: limit,
        });
        const responseData = data.map((run) => {
            const { aiJob: _aiJob, ...runDetails } = run;
            return runDetails;
        });
        return { data: responseData, totalInJob };
    }
    async getSpecificAiJobRun(jobId, runId) {
        const run = await this.aiJobsRunRepository.findOne({
            where: { id: runId, jobId },
        });
        if (!run)
            throw new common_1.NotFoundException(`AiJobsRun with ID ${runId} for job ${jobId} not found.`);
        const { aiJob: _aiJob, ...runDetails } = run;
        return runDetails;
    }
    async getVideosToCompareStatsByMonitoredVideo(shortcode) {
        const monitoredContent = await this.instaContentRepository.findOne({
            where: { code: shortcode, isMonitored: true },
            select: ['publishDate'],
        });
        if (!monitoredContent?.publishDate)
            throw new common_1.NotFoundException(`Monitored InstaContent with code ${shortcode} not found or has no publish date.`);
        const referenceDate = monitoredContent.publishDate;
        const whereClause = {
            isWatched: true,
            publishDate: (0, typeorm_2.MoreThanOrEqual)(referenceDate),
        };
        const total = await this.instaContentRepository.count({
            where: whereClause,
        });
        const downloaded = await this.instaContentRepository.count({
            where: { ...whereClause, isDownloaded: true },
        });
        const extracted = await this.instaContentRepository.count({
            where: { ...whereClause, isDownloaded: true, isExtracted: true },
        });
        return {
            publishedAt: referenceDate,
            total,
            downloaded,
            extracted,
        };
    }
    async getWatchedVideosStatsByDate(publishedDateInput) {
        const dateToCompare = publishedDateInput instanceof Date
            ? publishedDateInput
            : new Date(publishedDateInput);
        const whereClause = {
            isWatched: true,
            publishDate: (0, typeorm_2.MoreThanOrEqual)(dateToCompare),
        };
        const watchedVideosAfter = await this.instaContentRepository.count({
            where: whereClause,
        });
        const extractedVideosAfter = await this.instaContentRepository.count({
            where: { ...whereClause, isExtracted: true },
        });
        return {
            queryDate: dateToCompare,
            watchedVideosAfter,
            extractedVideosAfter,
        };
    }
    async getMonitoredContentGroupedByUser(queryDto) {
        const { offset = 0, limit = 10, search } = queryDto;
        const distinctUsernamesQb = this.instaContentRepository
            .createQueryBuilder('ic')
            .select('DISTINCT ic.username', 'username')
            .where('ic.isMonitored = :isMonitored', { isMonitored: true });
        if (search) {
            distinctUsernamesQb.andWhere('ic.username ILIKE :search', {
                search: `%${search}%`,
            });
        }
        const totalUsernames = await distinctUsernamesQb.getCount();
        if (totalUsernames === 0) {
            return { data: [], total: 0 };
        }
        const pagedUsernamesResult = await distinctUsernamesQb
            .orderBy('username', 'ASC')
            .offset(offset)
            .limit(limit)
            .getRawMany();
        const usernamesForPage = pagedUsernamesResult.map((u) => u.username);
        if (usernamesForPage.length === 0) {
            return { data: [], total: totalUsernames };
        }
        const videosData = await this.instaContentRepository.find({
            select: ['username', 'code', 'isExtracted'],
            where: {
                isMonitored: true,
                username: (0, typeorm_2.In)(usernamesForPage),
            },
            order: { username: 'ASC', createdAt: 'DESC' },
        });
        const groupedResult = [];
        let currentUserGroup = null;
        for (const video of videosData) {
            if (currentUserGroup?.username !== video.username) {
                currentUserGroup = { username: video.username, video_codes: [] };
                groupedResult.push(currentUserGroup);
            }
            currentUserGroup.video_codes.push({
                code: video.code,
                is_extracted: video.isExtracted,
            });
        }
        return { data: groupedResult, total: totalUsernames };
    }
    async getJobDefinitionPublishedDate(jobId) {
        const job = await this.aiJobRepository.findOne({
            where: { id: jobId },
            select: ['publishedDate'],
        });
        if (!job?.publishedDate)
            throw new common_1.NotFoundException(`AiJob with ID ${jobId} not found or has no published date.`);
        return job.publishedDate;
    }
    async updateJobThreshold(id, dto) {
        const job = await this.aiJobRepository.findOneBy({ id });
        if (!job)
            throw new common_1.NotFoundException(`AiJob with ID ${id} not found.`);
        if (dto.threshold === undefined) {
            throw new common_1.BadRequestException('Threshold must be provided for update.');
        }
        job.threshold = dto.threshold;
        try {
            const savedJob = await this.aiJobRepository.save(job);
            const { runs: _runs, ...jobDetails } = savedJob;
            return jobDetails;
        }
        catch (error) {
            this.logger.error(`Failed to update job ${id}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to update job.');
        }
    }
    async getJobThresholdValue(jobId) {
        const job = await this.aiJobRepository.findOne({
            where: { id: jobId },
            select: ['threshold'],
        });
        if (!job || typeof job.threshold !== 'number')
            throw new common_1.NotFoundException(`AiJob with ID ${jobId} not found or has no threshold.`);
        return job.threshold;
    }
    async getAllActiveJobsThresholds() {
        const jobs = await this.aiJobRepository.find({
            select: ['id', 'threshold'],
            where: { threshold: (0, typeorm_2.Not)((0, typeorm_2.IsNull)()) },
        });
        return jobs.reduce((acc, job) => {
            if (typeof job.threshold === 'number') {
                acc[job.id] = job.threshold;
            }
            return acc;
        }, {});
    }
    async getAggregatedEstimatedCostForJob(jobId) {
        await this.getAiJobDetails(jobId);
        const result = await this.aiJobsRunRepository
            .createQueryBuilder('run')
            .select('SUM(run.estimatedCost)', 'totalCost')
            .where('run.jobId = :jobId', { jobId })
            .andWhere('run.estimatedCost IS NOT NULL')
            .getRawOne();
        return parseFloat(result?.totalCost) || 0;
    }
    async getSpecificJobRunEstimatedCost(runId) {
        const run = await this.aiJobsRunRepository.findOne({
            where: { id: runId },
            select: ['estimatedCost'],
        });
        if (!run || typeof run.estimatedCost !== 'number')
            throw new common_1.NotFoundException(`AiJobsRun with ID ${runId} not found or has no estimated cost.`);
        return run.estimatedCost;
    }
    calculateEstimatedCostByComparisons(comparisons) {
        if (comparisons < 0)
            throw new common_1.BadRequestException('Number of comparisons cannot be negative.');
        return (0, utils_1.getSscdLambdaExpCost)(comparisons);
    }
    async getNewContentStatsRelativeToJobDate(jobId) {
        const job = await this.aiJobRepository.findOne({
            where: { id: jobId },
            select: ['publishedDate'],
        });
        if (!job?.publishedDate)
            throw new common_1.NotFoundException(`AiJob with ID ${jobId} not found or has no published date.`);
        const referenceDate = job.publishedDate;
        const baseConditions = (extraWhere = {}) => ({
            where: {
                publishDate: (0, typeorm_2.MoreThanOrEqual)(referenceDate),
                isWatched: true,
                ...extraWhere,
            },
        });
        const total = await this.instaContentRepository.count(baseConditions());
        const downloaded = await this.instaContentRepository.count(baseConditions({ isDownloaded: true }));
        const extracted = await this.instaContentRepository.count(baseConditions({ isExtracted: true, isDownloaded: true }));
        return { total, downloaded, extracted };
    }
    async getUsernameOfMonitoredVideoForJob(jobId) {
        const job = await this.aiJobRepository.findOne({
            where: { id: jobId },
            select: ['monitoredVideo'],
        });
        if (!job?.monitoredVideo)
            throw new common_1.NotFoundException(`AiJob with ID ${jobId} not found or has no monitored video code.`);
        const content = await this.instaContentRepository.findOne({
            where: { code: job.monitoredVideo },
            select: ['username'],
        });
        if (!content?.username)
            throw new common_1.NotFoundException(`InstaContent with code ${job.monitoredVideo} (from job ${jobId}) not found or has no username.`);
        return content.username;
    }
};
exports.AiJobsService = AiJobsService;
exports.AiJobsService = AiJobsService = AiJobsService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(ai_jobs_entity_1.AiJob)),
    __param(1, (0, typeorm_1.InjectRepository)(ai_jobs_run_entity_1.AiJobsRun)),
    __param(2, (0, typeorm_1.InjectRepository)(content_entity_1.InstaContent)),
    __param(3, (0, typeorm_1.InjectRepository)(ai_errors_entity_1.AiError)),
    __param(5, (0, common_1.Inject)(aws_module_1.SQS_SSCD_MODEL_SERVICE)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        config_1.ConfigService,
        aws_sqs_service_1.AwsSqsService])
], AiJobsService);
//# sourceMappingURL=ai-jobs.service.js.map