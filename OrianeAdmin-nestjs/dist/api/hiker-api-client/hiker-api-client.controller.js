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
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
var HikerController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.HikerController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const hiker_api_client_service_1 = require("./hiker-api-client.service");
const hiker_api_query_dto_1 = require("./dto/hiker-api-query.dto");
let HikerController = HikerController_1 = class HikerController {
    constructor(hikerApiService) {
        this.hikerApiService = hikerApiService;
        this.logger = new common_1.Logger(HikerController_1.name);
    }
    async getUserByUsername(username) {
        this.logger.log(`Request to get user by username: ${username}`);
        return this.hikerApiService.getUserByUsername(username);
    }
    async getUserClips(params) {
        this.logger.log(`Request to get user clips for user_id: ${params.user_id}, page_id: ${params.page_id}`);
        return this.hikerApiService.getUserClips(params.user_id, params.page_id);
    }
    async getUserMedias(params) {
        this.logger.log(`Request to get user medias for user_id: ${params.user_id}, page_id: ${params.page_id}`);
        return this.hikerApiService.getUserMedias(params.user_id, params.page_id);
    }
    async getUserStories(username) {
        this.logger.log(`Request to get user stories for username: ${username}`);
        return this.hikerApiService.getUserStories(username);
    }
    async getUserHighlights(userId) {
        this.logger.log(`Request to get user highlights for user_id: ${userId}`);
        return this.hikerApiService.getUserHighlights(userId);
    }
    async getUserFollowers(params) {
        this.logger.log(`Request to get user followers for user_id: ${params.user_id}, amount: ${params.amount}`);
        return this.hikerApiService.getUserFollowers(params.user_id, params.amount);
    }
    async getUserFollowing(params) {
        this.logger.log(`Request to get user following for user_id: ${params.user_id}, amount: ${params.amount}`);
        return this.hikerApiService.getUserFollowing(params.user_id, params.amount);
    }
    async getMediaById(id) {
        this.logger.log(`Request to get media info by ID: ${id}`);
        return this.hikerApiService.getMediaById(id);
    }
    async getMediaInfoByUrl(url) {
        this.logger.log(`Request to get media info by URL: ${url}`);
        return this.hikerApiService.getMediaInfoByUrl(url);
    }
    async getMediaInfoByCode(code) {
        this.logger.log(`Request to get media info by code: ${code}`);
        return this.hikerApiService.getMediaInfoByCode(code);
    }
    async getMediaComments(params) {
        this.logger.log(`Request to get media comments for mediaId: ${params.id}, page_id: ${params.page_id}`);
        return this.hikerApiService.getMediaComments(params.id, params.page_id);
    }
    async getMediaLikers(mediaId) {
        this.logger.log(`Request to get media likers for mediaId: ${mediaId}`);
        return this.hikerApiService.getMediaLikers(mediaId);
    }
    async getMediaTemplate(mediaId) {
        this.logger.log(`Request to get media template for mediaId: ${mediaId}`);
        return this.hikerApiService.getMediaTemplate(mediaId);
    }
    async getStoryById(storyId) {
        this.logger.log(`Request to get story by ID: ${storyId}`);
        return this.hikerApiService.getStoryById(storyId);
    }
    async getStoryByUrl(storyUrl) {
        this.logger.log(`Request to get story by URL: ${storyUrl}`);
        return this.hikerApiService.getStoryByUrl(storyUrl);
    }
    async getTrackById(trackId) {
        this.logger.log(`Request to get track by ID: ${trackId}`);
        return this.hikerApiService.getTrackById(trackId);
    }
    async getTrackByCanonicalId(canonicalId) {
        this.logger.log(`Request to get track by canonical ID: ${canonicalId}`);
        return this.hikerApiService.getTrackByCanonicalId(canonicalId);
    }
    async getTrackStreamById(trackId) {
        this.logger.log(`Request to get track stream by ID: ${trackId}`);
        return this.hikerApiService.getTrackStreamById(trackId);
    }
    async searchInstagramHandles(query) {
        this.logger.log(`Request to search Instagram handles with query: ${query}`);
        return this.hikerApiService.searchInstagramHandles(query);
    }
    async getHashtagByName(name) {
        this.logger.log(`Request to get hashtag by name: ${name}`);
        return this.hikerApiService.getHashtagByName(name);
    }
    async getHashtagTopMedias(hashtagId) {
        this.logger.log(`Request to get hashtag top medias for ID: ${hashtagId}`);
        return this.hikerApiService.getHashtagTopMedias(hashtagId);
    }
    async getHashtagRecentMedias(hashtagId) {
        this.logger.log(`Request to get hashtag recent medias for ID: ${hashtagId}`);
        return this.hikerApiService.getHashtagRecentMedias(hashtagId);
    }
    async getHashtagClipsMedias(hashtagId) {
        this.logger.log(`Request to get hashtag clips for ID: ${hashtagId}`);
        return this.hikerApiService.getHashtagClipsMedias(hashtagId);
    }
};
exports.HikerController = HikerController;
__decorate([
    (0, common_1.Get)('user/by-username'),
    (0, swagger_1.ApiOperation)({ summary: 'Get user profile by username' }),
    (0, swagger_1.ApiQuery)({
        name: 'username',
        type: String,
        required: true,
        description: 'The Instagram username',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'User details retrieved successfully.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 400,
        description: 'Bad request (e.g., missing username).',
    }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'User not found by Hiker API.' }),
    (0, swagger_1.ApiResponse)({ status: 502, description: 'Bad Gateway (Hiker API error).' }),
    __param(0, (0, common_1.Query)('username')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getUserByUsername", null);
__decorate([
    (0, common_1.Get)('user/clips'),
    (0, swagger_1.ApiOperation)({ summary: "Get user's clips (videos) by user_id" }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "User's clips retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [hiker_api_query_dto_1.GetUserMediaParamsDto]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getUserClips", null);
__decorate([
    (0, common_1.Get)('user/medias'),
    (0, swagger_1.ApiOperation)({ summary: "Get user's medias by user_id" }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "User's medias retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [hiker_api_query_dto_1.GetUserMediaParamsDto]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getUserMedias", null);
__decorate([
    (0, common_1.Get)('user/stories/by-username'),
    (0, swagger_1.ApiOperation)({ summary: "Get user's stories by username" }),
    (0, swagger_1.ApiQuery)({ name: 'username', type: String, required: true }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "User's stories retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)('username')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getUserStories", null);
__decorate([
    (0, common_1.Get)('user/highlights'),
    (0, swagger_1.ApiOperation)({ summary: "Get user's highlights by user_id" }),
    (0, swagger_1.ApiQuery)({ name: 'user_id', type: String, required: true }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "User's highlights retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)('user_id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getUserHighlights", null);
__decorate([
    (0, common_1.Get)('user/followers'),
    (0, swagger_1.ApiOperation)({ summary: "Get user's followers by user_id" }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "User's followers retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [hiker_api_query_dto_1.GetUserFollowsParamsDto]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getUserFollowers", null);
__decorate([
    (0, common_1.Get)('user/following'),
    (0, swagger_1.ApiOperation)({ summary: "Get user's following list by user_id" }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "User's following list retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [hiker_api_query_dto_1.GetUserFollowsParamsDto]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getUserFollowing", null);
__decorate([
    (0, common_1.Get)('media/info/by-id'),
    (0, swagger_1.ApiOperation)({ summary: 'Get media information by media ID' }),
    (0, swagger_1.ApiQuery)({
        name: 'id',
        type: String,
        required: true,
        description: "The media's unique ID",
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Media information retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getMediaById", null);
__decorate([
    (0, common_1.Get)('media/info/by-url'),
    (0, swagger_1.ApiOperation)({ summary: 'Get media information by media URL' }),
    (0, swagger_1.ApiQuery)({
        name: 'url',
        type: String,
        required: true,
        description: 'The URL of the media',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Media information retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('url')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getMediaInfoByUrl", null);
__decorate([
    (0, common_1.Get)('media/info/by-code'),
    (0, swagger_1.ApiOperation)({ summary: 'Get media information by media shortcode' }),
    (0, swagger_1.ApiQuery)({
        name: 'code',
        type: String,
        required: true,
        description: 'The shortcode of the media',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Media information retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getMediaInfoByCode", null);
__decorate([
    (0, common_1.Get)('media/comments'),
    (0, swagger_1.ApiOperation)({ summary: "Get media's comments by media ID" }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "Media's comments retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [hiker_api_query_dto_1.GetMediaCommentsParamsDto]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getMediaComments", null);
__decorate([
    (0, common_1.Get)('media/likers'),
    (0, swagger_1.ApiOperation)({ summary: 'Get list of likers for a media item' }),
    (0, swagger_1.ApiQuery)({
        name: 'id',
        type: String,
        required: true,
        description: "The media's unique ID",
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Media likers retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getMediaLikers", null);
__decorate([
    (0, common_1.Get)('media/template'),
    (0, swagger_1.ApiOperation)({ summary: 'Get media template by media ID' }),
    (0, swagger_1.ApiQuery)({
        name: 'mediaId',
        type: String,
        required: true,
        description: "The media's unique ID from Hiker API (often different from Instagram's media ID)",
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Media template retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('mediaId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getMediaTemplate", null);
__decorate([
    (0, common_1.Get)('story/by-id'),
    (0, swagger_1.ApiOperation)({ summary: 'Get story by story ID' }),
    (0, swagger_1.ApiQuery)({
        name: 'storyId',
        type: String,
        required: true,
        description: "The story's unique ID",
    }),
    (0, swagger_1.ApiResponse)({ status: 200, description: 'Story retrieved successfully.' }),
    __param(0, (0, common_1.Query)('storyId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getStoryById", null);
__decorate([
    (0, common_1.Get)('story/by-url'),
    (0, swagger_1.ApiOperation)({ summary: 'Get story by story URL' }),
    (0, swagger_1.ApiQuery)({
        name: 'storyUrl',
        type: String,
        required: true,
        description: 'The URL of the story',
    }),
    (0, swagger_1.ApiResponse)({ status: 200, description: 'Story retrieved successfully.' }),
    __param(0, (0, common_1.Query)('storyUrl')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getStoryByUrl", null);
__decorate([
    (0, common_1.Get)('track/by-id'),
    (0, swagger_1.ApiOperation)({ summary: 'Get track information by track ID' }),
    (0, swagger_1.ApiQuery)({ name: 'trackId', type: String, required: true }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Track information retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('trackId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getTrackById", null);
__decorate([
    (0, common_1.Get)('track/by-canonical-id'),
    (0, swagger_1.ApiOperation)({ summary: 'Get track information by canonical ID' }),
    (0, swagger_1.ApiQuery)({ name: 'canonicalId', type: String, required: true }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Track information retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('canonicalId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getTrackByCanonicalId", null);
__decorate([
    (0, common_1.Get)('track/stream/by-id'),
    (0, swagger_1.ApiOperation)({ summary: 'Get track stream by track ID' }),
    (0, swagger_1.ApiQuery)({ name: 'trackId', type: String, required: true }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Track stream retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('trackId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getTrackStreamById", null);
__decorate([
    (0, common_1.Get)('search/users'),
    (0, swagger_1.ApiOperation)({ summary: 'Search for Instagram users/handles' }),
    (0, swagger_1.ApiQuery)({
        name: 'query',
        type: String,
        required: true,
        description: 'Search query for usernames',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Search results retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('query')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "searchInstagramHandles", null);
__decorate([
    (0, common_1.Get)('hashtag/by-name'),
    (0, swagger_1.ApiOperation)({ summary: 'Get hashtag information by name' }),
    (0, swagger_1.ApiQuery)({
        name: 'name',
        type: String,
        required: true,
        description: "The name of the hashtag (without '#')",
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Hashtag information retrieved successfully.',
    }),
    __param(0, (0, common_1.Query)('name')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getHashtagByName", null);
__decorate([
    (0, common_1.Get)('hashtag/medias/top'),
    (0, swagger_1.ApiOperation)({ summary: "Get a hashtag's top medias by hashtag ID" }),
    (0, swagger_1.ApiQuery)({ name: 'hashtagId', type: String, required: true }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "Hashtag's top medias retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)('hashtagId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getHashtagTopMedias", null);
__decorate([
    (0, common_1.Get)('hashtag/medias/recent'),
    (0, swagger_1.ApiOperation)({ summary: "Get a hashtag's recent medias by hashtag ID" }),
    (0, swagger_1.ApiQuery)({ name: 'hashtagId', type: String, required: true }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "Hashtag's recent medias retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)('hashtagId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getHashtagRecentMedias", null);
__decorate([
    (0, common_1.Get)('hashtag/medias/clips'),
    (0, swagger_1.ApiOperation)({ summary: "Get a hashtag's clips by hashtag ID" }),
    (0, swagger_1.ApiQuery)({ name: 'hashtagId', type: String, required: true }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: "Hashtag's clips retrieved successfully.",
    }),
    __param(0, (0, common_1.Query)('hashtagId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HikerController.prototype, "getHashtagClipsMedias", null);
exports.HikerController = HikerController = HikerController_1 = __decorate([
    (0, swagger_1.ApiTags)('Instagram Collector'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('instagram-collector'),
    __metadata("design:paramtypes", [hiker_api_client_service_1.HikerApiClientService])
], HikerController);
//# sourceMappingURL=hiker-api-client.controller.js.map