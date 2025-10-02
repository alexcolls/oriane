import { AiJobsRun } from '../../../../entities/ai-jobs-run.entity';
import { AiJob } from '../../../../entities/ai-jobs.entity';
declare const CreateAiJobsRunInternalDto_base: import("@nestjs/common").Type<Pick<AiJobsRun, "jobId" | "comparisonsToProcess" | "startedAt" | "state" | "estimatedCost">>;
export declare class CreateAiJobsRunInternalDto extends CreateAiJobsRunInternalDto_base {
    aiJob?: AiJob;
}
declare const UpdateAiJobsRunInternalDto_base: import("@nestjs/common").Type<Partial<Pick<AiJobsRun, "comparisonsProcessed" | "comparisonsFailed" | "lastVideoCode" | "lastPublishedDate" | "finishedAt" | "state" | "warningsCount">>>;
export declare class UpdateAiJobsRunInternalDto extends UpdateAiJobsRunInternalDto_base {
}
declare const AiJobsRunBasicResponseDto_base: import("@nestjs/common").Type<Pick<AiJobsRun, "id" | "createdAt" | "jobId" | "comparisonsToProcess" | "comparisonsProcessed" | "comparisonsFailed" | "lastVideoCode" | "lastPublishedDate" | "startedAt" | "finishedAt" | "state" | "warningsCount" | "estimatedCost">>;
export declare class AiJobsRunBasicResponseDto extends AiJobsRunBasicResponseDto_base {
}
export declare class GetAiJobRunsResponseDto {
    data: AiJobsRunBasicResponseDto[];
    totalInJob: number;
}
export {};
