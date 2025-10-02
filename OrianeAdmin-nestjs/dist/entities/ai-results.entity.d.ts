import { AiJob } from './ai-jobs.entity';
import { AiJobsRun } from './ai-jobs-run.entity';
import { InstaContent } from './content.entity';
export declare class AiResult {
    id: string;
    jobId: string | null;
    aiJob?: AiJob | null;
    createdAt: Date;
    monitoredVideo: string;
    monitoredInstaContent?: InstaContent;
    watchedVideo: string;
    watchedInstaContent?: InstaContent;
    avgSimilarity: number | null;
    processedInSecs: number | null;
    frameResults: Array<{
        frame_number: number;
        similarity: number;
    }> | null;
    maxSimilarity: number | null;
    model: string;
    similarity: number;
    stdSimilarity: number | null;
    jobRunId: string | null;
    aiJobsRun?: AiJobsRun | null;
}
