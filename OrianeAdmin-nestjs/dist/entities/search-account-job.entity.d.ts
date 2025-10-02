import { SearchAccountResult } from './search-account-result.entity';
export declare enum SearchAccountJobStatus {
    PENDING = "pending",
    PROCESSING = "processing",
    COMPLETED = "completed",
    FAILED = "failed"
}
export declare class SearchAccountJob {
    id: string;
    createdAt: Date;
    updatedAt: Date;
    status: SearchAccountJobStatus;
    keywords: string[];
    totalKeywords: number;
    processedKeywords: number;
    totalFoundAccounts: number;
    filteredAccounts: number;
    csvFileUrl: string;
    errorMessage: string;
    jobData: any;
    startedAt: Date;
    completedAt: Date;
    results: SearchAccountResult[];
}
