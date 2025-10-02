import { SearchAccountJobStatus } from '../../../entities/search-account-job.entity';
export declare class BulkSearchAccountsDto {
    keywords: string[];
    resultsPerKeyword?: number;
    minFollowers?: number;
    maxFollowers?: number;
    minPostsInLastMonth?: number;
    requireVerified?: boolean;
    requireBusiness?: boolean;
    includePrivateAccounts?: boolean;
}
export declare class BulkSearchResponseDto {
    searchAccountsId: string;
    status: SearchAccountJobStatus;
    totalKeywords: number;
    estimatedTimeMinutes: number;
    message: string;
}
export declare class SearchJobStatusDto {
    searchAccountsId: string;
    status: SearchAccountJobStatus;
    createdAt: Date;
    startedAt?: Date;
    completedAt?: Date;
    totalKeywords: number;
    processedKeywords: number;
    totalFoundAccounts: number;
    filteredAccounts: number;
    csvFileUrl?: string;
    progressPercentage: number;
    errorMessage?: string;
    estimatedTimeRemainingMinutes?: number;
}
export declare class CsvSearchAccountsDto {
    resultsPerKeyword?: number;
    minFollowers?: number;
    maxFollowers?: number;
    minPostsInLastMonth?: number;
    requireVerified?: boolean;
    requireBusiness?: boolean;
    includePrivateAccounts?: boolean;
}
export interface FilteredAccountData {
    keyword: string;
    username: string;
    userPk: string;
    fullName: string;
    followerCount: number;
    followingCount: number;
    mediaCount: number;
    isVerified: boolean;
    isBusiness: boolean;
    category: string;
    biography: string;
    externalUrl: string;
}
