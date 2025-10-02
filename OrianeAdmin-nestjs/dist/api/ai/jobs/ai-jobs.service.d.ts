import { ConfigService } from '@nestjs/config';
import { Repository } from 'typeorm';
import { AwsSqsService } from '../../../aws/aws.sqs.service';
import { AiJob } from '../../../entities/ai-jobs.entity';
import { AiJobsRun } from '../../../entities/ai-jobs-run.entity';
import { InstaContent } from '../../../entities/content.entity';
import { AiError } from '../../../entities/ai-errors.entity';
import { GetAiJobsQueryDto, GetAiJobsResponseDto, UpdateAiJobDto, QueueAiJobDto, GetMonitoredVideosResponseDto, AiJobBasicResponseDto } from './dto/ai-jobs.dto';
import { AiJobsRunBasicResponseDto, GetAiJobRunsResponseDto } from './dto/ai-jobs-run.dto';
export declare class AiJobsService {
    private readonly aiJobRepository;
    private readonly aiJobsRunRepository;
    private readonly instaContentRepository;
    private readonly aiErrorRepository;
    private readonly configService;
    private readonly awsSqsService;
    private readonly logger;
    private readonly debug;
    constructor(aiJobRepository: Repository<AiJob>, aiJobsRunRepository: Repository<AiJobsRun>, instaContentRepository: Repository<InstaContent>, aiErrorRepository: Repository<AiError>, configService: ConfigService, awsSqsService: AwsSqsService);
    private internalCreateNewAiJob;
    startJobWorkflow(dto: QueueAiJobDto): Promise<{
        aiJob: AiJobBasicResponseDto;
        aiJobRun: AiJobsRunBasicResponseDto;
    }>;
    private executeJobRunLogic;
    private processAndDispatchRunBatches;
    private fetchInstaContentForRun;
    private dispatchSqsBatch;
    private buildSqsPayload;
    private recordErrorForRun;
    getAiJobs(queryDto: GetAiJobsQueryDto): Promise<GetAiJobsResponseDto>;
    verifyAiJobExists(monitoredVideo: string, model: string, useGpu: boolean): Promise<boolean>;
    getAiJobDetails(id: string): Promise<AiJobBasicResponseDto>;
    getAiJobsByMonitoredVideoCode(code: string): Promise<AiJobBasicResponseDto[]>;
    updateAiJobDefinition(id: string, dto: UpdateAiJobDto): Promise<AiJobBasicResponseDto>;
    patchAiJobDefinition(id: string, dto: Partial<UpdateAiJobDto>): Promise<AiJobBasicResponseDto>;
    deleteAiJob(id: string): Promise<void>;
    getLastAiJobRunForJob(jobId: string): Promise<AiJobsRun | null>;
    getAllRunsForJob(jobId: string, queryDto: GetAiJobsQueryDto): Promise<GetAiJobRunsResponseDto>;
    getSpecificAiJobRun(jobId: string, runId: string): Promise<AiJobsRunBasicResponseDto>;
    getVideosToCompareStatsByMonitoredVideo(shortcode: string): Promise<{
        publishedAt: Date;
        total: number;
        downloaded: number;
        extracted: number;
    }>;
    getWatchedVideosStatsByDate(publishedDateInput: Date): Promise<{
        queryDate: Date;
        watchedVideosAfter: number;
        extractedVideosAfter: number;
    }>;
    getMonitoredContentGroupedByUser(queryDto: GetAiJobsQueryDto): Promise<GetMonitoredVideosResponseDto>;
    getJobDefinitionPublishedDate(jobId: string): Promise<Date>;
    updateJobThreshold(id: string, dto: UpdateAiJobDto): Promise<AiJobBasicResponseDto>;
    getJobThresholdValue(jobId: string): Promise<number>;
    getAllActiveJobsThresholds(): Promise<Record<string, number>>;
    getAggregatedEstimatedCostForJob(jobId: string): Promise<number>;
    getSpecificJobRunEstimatedCost(runId: string): Promise<number>;
    calculateEstimatedCostByComparisons(comparisons: number): number;
    getNewContentStatsRelativeToJobDate(jobId: string): Promise<{
        total: number;
        downloaded: number;
        extracted: number;
    }>;
    getUsernameOfMonitoredVideoForJob(jobId: string): Promise<string>;
}
