import { SearchAccountJob } from './search-account-job.entity';
export declare class SearchAccountResult {
    id: string;
    createdAt: Date;
    jobId: string;
    keyword: string;
    username: string;
    userPk: string;
    fullName: string;
    isPrivate: boolean;
    profilePicUrl: string;
    isVerified: boolean;
    mediaCount: number;
    followerCount: number;
    followingCount: number;
    biography: string;
    externalUrl: string;
    accountType: string;
    isBusiness: boolean;
    category: string;
    passedFilter: boolean;
    filterReason: string;
    job: SearchAccountJob;
}
