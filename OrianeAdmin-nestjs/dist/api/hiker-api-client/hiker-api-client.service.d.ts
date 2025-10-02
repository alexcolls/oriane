import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
export interface HikerUserProfile {
    user: {
        public_email: any;
        pk: string;
        username: string;
        full_name: string;
        is_private: boolean;
        profile_pic_url: string;
        profile_pic_url_hd: string;
        is_verified: boolean;
        media_count: number;
        follower_count: number;
        following_count: number;
        biography: string;
        external_url: string;
        account_type: string;
        is_business: boolean;
        category: string;
        average_like_count: number;
        average_comment_count: number;
    };
}
export declare class HikerApiClientService {
    private readonly httpService;
    private readonly configService;
    private readonly baseUrl;
    private readonly apiKey;
    private readonly logger;
    constructor(httpService: HttpService, configService: ConfigService);
    private handleApiError;
    private getRequestConfig;
    getUserByUsername(username: string): Promise<HikerUserProfile>;
    getUserClips(userId: string, pageId?: string): Promise<any>;
    getUserMedias(userId: string, pageId?: string): Promise<any>;
    getUserStories(username: string): Promise<any>;
    getUserHighlights(userId: string): Promise<any>;
    getUserFollowers(userId: string, amount?: number): Promise<any>;
    getUserFollowing(userId: string, amount?: number): Promise<any>;
    getMediaById(id: string): Promise<any>;
    getMediaInfoByUrl(url: string): Promise<any>;
    getMediaComments(mediaId: string, pageId?: string): Promise<any>;
    getMediaLikers(mediaId: string): Promise<any>;
    getMediaTemplate(mediaId: string): Promise<any>;
    getStoryById(storyId: string): Promise<any>;
    getStoryByUrl(storyUrl: string): Promise<any>;
    getTrackByCanonicalId(canonicalId: string): Promise<any>;
    getTrackById(trackId: string): Promise<any>;
    getTrackStreamById(trackId: string): Promise<any>;
    searchInstagramHandles(query: string): Promise<any>;
    getHashtagByName(name: string): Promise<any>;
    getHashtagTopMedias(hashtagId: string): Promise<any>;
    getHashtagRecentMedias(hashtagId: string): Promise<any>;
    getHashtagClipsMedias(hashtagId: string): Promise<any>;
    searchAccountsV2(query: string, count?: number): Promise<any>;
    getMediaInfoByCode(code: string): Promise<any>;
}
