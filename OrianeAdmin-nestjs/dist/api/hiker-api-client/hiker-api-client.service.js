"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var HikerApiClientService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.HikerApiClientService = void 0;
const common_1 = require("@nestjs/common");
const axios_1 = require("@nestjs/axios");
const config_1 = require("@nestjs/config");
const rxjs_1 = require("rxjs");
let HikerApiClientService = HikerApiClientService_1 = class HikerApiClientService {
    constructor(httpService, configService) {
        this.httpService = httpService;
        this.configService = configService;
        this.logger = new common_1.Logger(HikerApiClientService_1.name);
        this.baseUrl = this.configService.get('HIKER_API_URL');
        this.apiKey = this.configService.get('HIKER_API_KEY');
        if (!this.baseUrl || !this.apiKey) {
            this.logger.error('HIKER_API_URL or HIKER_API_KEY is not configured!');
        }
    }
    async handleApiError(error, operation) {
        this.logger.error(`Error during Hiker API operation "${operation}": ${error.message}`, error.response?.data || error.stack);
        let statusCode = common_1.HttpStatus.BAD_GATEWAY;
        let message = `Hiker API Error: Operation "${operation}" failed.`;
        if (error.response) {
            message += ` Status: ${error.response.status}. Response: ${JSON.stringify(error.response.data)}`;
            if (error.response.status === common_1.HttpStatus.NOT_FOUND) {
                statusCode = common_1.HttpStatus.NOT_FOUND;
            }
            else if (error.response.status === common_1.HttpStatus.UNAUTHORIZED ||
                error.response.status === common_1.HttpStatus.FORBIDDEN) {
                statusCode = common_1.HttpStatus.UNAUTHORIZED;
            }
        }
        throw new common_1.HttpException(message, statusCode);
    }
    getRequestConfig(params) {
        return {
            params,
            headers: { 'x-access-key': this.apiKey },
        };
    }
    async getUserByUsername(username) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/user/by/username`, this.getRequestConfig({ username })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getUserByUsername');
        }
    }
    async getUserClips(userId, pageId) {
        const params = { user_id: userId };
        if (pageId) {
            params.page_id = pageId;
        }
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/user/clips`, this.getRequestConfig(params)));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getUserClips');
        }
    }
    async getUserMedias(userId, pageId) {
        const params = { user_id: userId };
        if (pageId) {
            params.page_id = pageId;
        }
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/user/medias`, this.getRequestConfig(params)));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getUserMedias');
        }
    }
    async getUserStories(username) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/user/stories/by/username`, this.getRequestConfig({ username })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getUserStories');
        }
    }
    async getUserHighlights(userId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/user/highlights`, this.getRequestConfig({ user_id: userId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getUserHighlights');
        }
    }
    async getUserFollowers(userId, amount) {
        const params = { user_id: userId };
        if (amount !== undefined)
            params.amount = amount;
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/user/followers`, this.getRequestConfig(params)));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getUserFollowers');
        }
    }
    async getUserFollowing(userId, amount) {
        const params = { user_id: userId };
        if (amount !== undefined)
            params.amount = amount;
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/user/following`, this.getRequestConfig(params)));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getUserFollowing');
        }
    }
    async getMediaById(id) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/media/info/by/id`, this.getRequestConfig({ id })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getMediaById');
        }
    }
    async getMediaInfoByUrl(url) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/media/info/by/url`, this.getRequestConfig({ url })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getMediaInfoByUrl');
        }
    }
    async getMediaComments(mediaId, pageId) {
        const params = { id: mediaId };
        if (pageId) {
            params.page_id = pageId;
        }
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/media/comments`, this.getRequestConfig(params)));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getMediaComments');
        }
    }
    async getMediaLikers(mediaId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/media/likers`, this.getRequestConfig({ id: mediaId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getMediaLikers');
        }
    }
    async getMediaTemplate(mediaId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/media/template`, this.getRequestConfig({ media_id: mediaId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getMediaTemplate');
        }
    }
    async getStoryById(storyId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/story/by/id`, this.getRequestConfig({ story_id: storyId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getStoryById');
        }
    }
    async getStoryByUrl(storyUrl) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/story/by/url`, this.getRequestConfig({ story_url: storyUrl })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getStoryByUrl');
        }
    }
    async getTrackByCanonicalId(canonicalId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/track/by/canonical/id`, this.getRequestConfig({ canonical_id: canonicalId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getTrackByCanonicalId');
        }
    }
    async getTrackById(trackId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/track/by/id`, this.getRequestConfig({ track_id: trackId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getTrackById');
        }
    }
    async getTrackStreamById(trackId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/track/stream/by/id`, this.getRequestConfig({ track_id: trackId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getTrackStreamById');
        }
    }
    async searchInstagramHandles(query) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/search/users`, this.getRequestConfig({ query })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'searchInstagramHandles');
        }
    }
    async getHashtagByName(name) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/hashtag/by/name`, this.getRequestConfig({ name })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getHashtagByName');
        }
    }
    async getHashtagTopMedias(hashtagId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/hashtag/medias/top`, this.getRequestConfig({ hashtag_id: hashtagId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getHashtagTopMedias');
        }
    }
    async getHashtagRecentMedias(hashtagId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/hashtag/medias/recent`, this.getRequestConfig({ hashtag_id: hashtagId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getHashtagRecentMedias');
        }
    }
    async getHashtagClipsMedias(hashtagId) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/hashtag/medias/clips`, this.getRequestConfig({ hashtag_id: hashtagId })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getHashtagClipsMedias');
        }
    }
    async searchAccountsV2(query, count = 100) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/search/accounts`, this.getRequestConfig({ query, count })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'searchAccountsV2');
        }
    }
    async getMediaInfoByCode(code) {
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService.get(`${this.baseUrl}/v2/media/info/by/code`, this.getRequestConfig({ code })));
            return response.data;
        }
        catch (error) {
            return this.handleApiError(error, 'getMediaInfoByCode');
        }
    }
};
exports.HikerApiClientService = HikerApiClientService;
exports.HikerApiClientService = HikerApiClientService = HikerApiClientService_1 = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [axios_1.HttpService,
        config_1.ConfigService])
], HikerApiClientService);
//# sourceMappingURL=hiker-api-client.service.js.map