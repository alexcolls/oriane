import { AiJobsRun } from './ai-jobs-run.entity';
export declare class AiJob {
    id: string;
    createdAt: Date;
    model: string;
    useGpu: boolean;
    monitoredVideo: string;
    publishedDate: Date;
    threshold: number;
    runs: AiJobsRun[];
}
