export declare class SearchAccountsByKeywordDto {
    keyword: string;
    count?: number;
}
export interface SearchAccountResult {
    user: {
        pk: string;
        username: string;
        full_name: string;
        is_private: boolean;
        profile_pic_url?: string;
        is_verified: boolean;
        media_count: number;
        follower_count: number;
        following_count: number;
        biography?: string;
        external_url?: string;
        account_type?: string;
        is_business: boolean;
        category?: string;
    };
}
