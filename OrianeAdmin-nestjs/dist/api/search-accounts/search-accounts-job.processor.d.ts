import { Repository } from 'typeorm';
import { HikerApiClientService } from '../hiker-api-client/hiker-api-client.service';
import { SearchAccountJob } from '../../entities/search-account-job.entity';
import { SearchAccountResult } from '../../entities/search-account-result.entity';
export interface BulkSearchJobData {
    jobId: string;
    keywords: string[];
    resultsPerKeyword: number;
    minFollowerCount: number;
    maxFollowerCount?: number;
    includePrivateAccounts: boolean;
    minMediaCount: number;
    requireVerified: boolean;
    requireBusiness: boolean;
}
export declare class SearchAccountsJobProcessor {
    private readonly searchJobRepository;
    private readonly searchResultRepository;
    private readonly hikerApiService;
    private readonly logger;
    private readonly DAYS_THRESHOLD;
    constructor(searchJobRepository: Repository<SearchAccountJob>, searchResultRepository: Repository<SearchAccountResult>, hikerApiService: HikerApiClientService);
    processPendingJobs(): Promise<void>;
    private applyFilters;
    private getRecentMediaCount;
    private updateJobStatus;
    private updateJobProgress;
    private completeJob;
    private failJob;
    private sleep;
}
