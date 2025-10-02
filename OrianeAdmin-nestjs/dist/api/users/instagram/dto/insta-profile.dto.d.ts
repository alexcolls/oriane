export declare class CreateInstaProfileDto {
    username: string;
    platform: string | null;
    isVerified: boolean | null;
    biography: string | null;
    profilePic: string | null;
    followersCount: number | null;
    followingCount: number | null;
    engagementRate: number | null;
    averageLikes: number | null;
    averageComments: number | null;
    accountType: string | null;
    isBusinessAccount: boolean | null;
    category: string | null;
    externalUrl: string | null;
    publicEmail: string | null;
    lastPostDate: Date | null;
    accountRef: string | null;
    isTracked: boolean | null;
    isOnboarded: boolean | null;
    fullName: string | null;
    isPrivate: boolean | null;
    mediaCount: number | null;
    orianeUserId: string | null;
    userId: string | null;
}
declare const UpdateInstaProfileDto_base: import("@nestjs/common").Type<Partial<CreateInstaProfileDto>>;
export declare class UpdateInstaProfileDto extends UpdateInstaProfileDto_base {
}
export declare class GetInstaProfilesQueryDto {
    isCreator?: boolean;
    offset?: number;
    limit?: number;
}
import { InstaProfile } from '../../../../entities/insta-profiles.entity';
declare const InstaProfileResponseDto_base: import("@nestjs/common").Type<Omit<InstaProfile, "orianeUser" | "contents">>;
export declare class InstaProfileResponseDto extends InstaProfileResponseDto_base {
}
export {};
