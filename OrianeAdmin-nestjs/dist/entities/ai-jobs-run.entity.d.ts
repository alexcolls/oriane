import { AiJob } from './ai-jobs.entity';
export declare class AiJobsRun {
    id: string;
    createdAt: Date;
    jobId: string;
    aiJob: AiJob;
    comparisonsToProcess: number;
    comparisonsProcessed: number;
    comparisonsFailed: number;
    lastVideoCode: string | null;
    lastPublishedDate: Date | null;
    startedAt: Date | null;
    finishedAt: Date | null;
    state: string;
    warningsCount: number;
    estimatedCost: number;
}
