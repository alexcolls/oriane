import { InstaProfile } from './insta-profiles.entity';
export type UserPriority = 'low' | 'medium' | 'high';
export type AccountStatus = 'Pending' | 'Active' | 'Checked' | 'Error' | 'Deactivated' | 'Unchecked';
export declare class OrianeUser {
    id: string;
    nextCheckAt: Date | null;
    checkFrequency: number;
    priority: UserPriority | null;
    environment: string;
    lastCursor: Date | null;
    lastChecked: Date | null;
    username: string;
    isCreator: boolean;
    isDeactivated: boolean | null;
    stateError: boolean | null;
    accountStatus: AccountStatus | null;
    errorMessage: string | null;
    isWatched: boolean;
    firstFetched: Date | null;
    createdAt: Date | null;
    lastFetched: Date | null;
    instaProfiles: InstaProfile[];
}
