import { AiJobsService } from './ai-jobs.service';
import { GetAiJobsQueryDto, GetAiJobsResponseDto, UpdateAiJobDto, QueueAiJobDto, GetMonitoredVideosResponseDto, AiJobBasicResponseDto } from './dto/ai-jobs.dto';
import { AiJobsRunBasicResponseDto, GetAiJobRunsResponseDto } from './dto/ai-jobs-run.dto';
export declare class AiJobsController {
    private readonly aiJobsService;
    private readonly logger;
    constructor(aiJobsService: AiJobsService);
    startJobWorkflow(dto: QueueAiJobDto): Promise<{
        aiJob: AiJobBasicResponseDto;
        aiJobRun: AiJobsRunBasicResponseDto;
    }>;
    getAiJobDefinitions(queryDto: GetAiJobsQueryDto): Promise<GetAiJobsResponseDto>;
    getAiJobDetails(id: string): Promise<AiJobBasicResponseDto>;
    getAiJobsByMonitoredVideoCode(code: string): Promise<AiJobBasicResponseDto[]>;
    patchAiJobDefinition(id: string, updateDto: UpdateAiJobDto): Promise<AiJobBasicResponseDto>;
    deleteAiJob(id: string): Promise<void>;
    getAllRunsForJob(jobId: string, queryDto: GetAiJobsQueryDto): Promise<GetAiJobRunsResponseDto>;
    getSpecificAiJobRun(jobId: string, runId: string): Promise<AiJobsRunBasicResponseDto>;
    getVideosToCompareStatsByMonitoredVideo(shortcode: string): Promise<{
        publishedAt: Date;
        total: number;
        downloaded: number;
        extracted: number;
    }>;
    getMonitoredContentGroupedByUser(queryDto: GetAiJobsQueryDto): Promise<GetMonitoredVideosResponseDto>;
    updateAiJobThreshold(id: string, updateDto: {
        threshold: number;
    }): Promise<AiJobBasicResponseDto>;
    getJobThresholdValue(id: string): Promise<number>;
    getAggregatedEstimatedCostForJob(id: string): Promise<number>;
    getSpecificJobRunEstimatedCost(runId: string): Promise<number>;
    getUsernameOfMonitoredVideoForJob(id: string): Promise<string>;
    getJobDefinitionPublishedDate(id: string): Promise<Date>;
    getNewContentStatsRelativeToJobDate(id: string): Promise<{
        total: number;
        downloaded: number;
        extracted: number;
    }>;
    getAllActiveJobsThresholds(): Promise<Record<string, number>>;
    calculateEstimatedCostByComparisons(comparisons: number): Promise<number>;
}
