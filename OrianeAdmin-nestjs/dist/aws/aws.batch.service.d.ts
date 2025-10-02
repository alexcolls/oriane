export declare class BatchService {
    private client;
    submitSingleExtractionJob(videoCode: string): Promise<string>;
    waitForJobs(jobIds: string[]): Promise<void>;
}
