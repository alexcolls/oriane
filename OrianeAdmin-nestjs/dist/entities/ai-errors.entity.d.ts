import { AiJob } from './ai-jobs.entity';
import { AiJobsRun } from './ai-jobs-run.entity';
export declare class AiError {
    id: string;
    createdAt: Date;
    jobId: string;
    aiJob: AiJob;
    watchedVideo: string;
    errorMessage: string;
    jobRunId: string | null;
    aiJobsRun?: AiJobsRun | null;
}
