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
var InstaProfilesController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.InstaProfilesController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const insta_profiles_service_1 = require("./insta-profiles.service");
const insta_profile_dto_1 = require("./dto/insta-profile.dto");
let InstaProfilesController = InstaProfilesController_1 = class InstaProfilesController {
    constructor(profilesService) {
        this.profilesService = profilesService;
        this.logger = new common_1.Logger(InstaProfilesController_1.name);
    }
    async getAllProfiles(queryDto) {
        this.logger.log(`Workspaceing all profiles. Query: ${JSON.stringify(queryDto)}`);
        const profiles = await this.profilesService.getAllProfiles(queryDto.isCreator);
        return profiles.map((p) => {
            const { orianeUser: _orianeUser, contents: _contents, ...response } = p;
            return response;
        });
    }
    async getProfileByUsername(username) {
        this.logger.log(`Workspaceing profile for username: ${username}`);
        const profile = await this.profilesService.getProfileByUsername(username);
        const { orianeUser: _orianeUser, contents: _contents, ...response } = profile;
        return response;
    }
    async getProfileById(id) {
        this.logger.log(`Workspaceing profile for ID: ${id}`);
        const profile = await this.profilesService.getProfileById(id);
        const { orianeUser: _orianeUser, contents: _contents, ...response } = profile;
        return response;
    }
    async createProfile(createProfileDto) {
        this.logger.log(`Attempting to create profile for username: ${createProfileDto.username}`);
        const profile = await this.profilesService.createProfile(createProfileDto);
        const { orianeUser: _orianeUser, contents: _contents, ...response } = profile;
        return response;
    }
    async updateProfile(id, updateData) {
        this.logger.log(`Attempting to update profile with ID: ${id}`);
        const profile = await this.profilesService.updateProfile(id, updateData);
        const { orianeUser: _orianeUser, contents: _contents, ...response } = profile;
        return response;
    }
    async deleteProfile(id) {
        this.logger.log(`Attempting to delete profile with ID: ${id}`);
        await this.profilesService.deleteProfile(id);
    }
};
exports.InstaProfilesController = InstaProfilesController;
__decorate([
    (0, common_1.Get)(),
    (0, swagger_1.ApiOperation)({ summary: 'Get all Instagram profiles, optionally filtered.' }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'List of Instagram profiles.',
        type: [insta_profile_dto_1.InstaProfileResponseDto],
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [insta_profile_dto_1.GetInstaProfilesQueryDto]),
    __metadata("design:returntype", Promise)
], InstaProfilesController.prototype, "getAllProfiles", null);
__decorate([
    (0, common_1.Get)('by-username/:username'),
    (0, swagger_1.ApiOperation)({ summary: 'Get a specific Instagram profile by username.' }),
    (0, swagger_1.ApiParam)({
        name: 'username',
        description: 'Instagram username',
        type: String,
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Instagram profile data.',
        type: insta_profile_dto_1.InstaProfileResponseDto,
    }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'Profile not found.' }),
    __param(0, (0, common_1.Param)('username')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], InstaProfilesController.prototype, "getProfileByUsername", null);
__decorate([
    (0, common_1.Get)('by-id/:id'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get a specific Instagram profile by its database ID.',
    }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'Profile UUID',
        type: String,
        format: 'uuid',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Instagram profile data.',
        type: insta_profile_dto_1.InstaProfileResponseDto,
    }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'Profile not found.' }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], InstaProfilesController.prototype, "getProfileById", null);
__decorate([
    (0, common_1.Post)(),
    (0, swagger_1.ApiOperation)({ summary: 'Create a new Instagram profile.' }),
    (0, swagger_1.ApiBody)({ type: insta_profile_dto_1.CreateInstaProfileDto }),
    (0, swagger_1.ApiResponse)({
        status: 201,
        description: 'Profile created successfully.',
        type: insta_profile_dto_1.InstaProfileResponseDto,
    }),
    (0, swagger_1.ApiResponse)({ status: 400, description: 'Invalid input data.' }),
    (0, swagger_1.ApiResponse)({
        status: 409,
        description: 'Profile with this username already exists.',
    }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [insta_profile_dto_1.CreateInstaProfileDto]),
    __metadata("design:returntype", Promise)
], InstaProfilesController.prototype, "createProfile", null);
__decorate([
    (0, common_1.Put)(':id'),
    (0, swagger_1.ApiOperation)({
        summary: 'Update/Replace an existing Instagram profile by ID.',
    }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'UUID of the profile to update',
        type: String,
        format: 'uuid',
    }),
    (0, swagger_1.ApiBody)({ type: insta_profile_dto_1.CreateInstaProfileDto }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Profile updated successfully.',
        type: insta_profile_dto_1.InstaProfileResponseDto,
    }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'Profile not found.' }),
    (0, swagger_1.ApiResponse)({ status: 400, description: 'Invalid input data.' }),
    (0, swagger_1.ApiResponse)({
        status: 409,
        description: 'Conflict (e.g. username already taken).',
    }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __param(1, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, insta_profile_dto_1.UpdateInstaProfileDto]),
    __metadata("design:returntype", Promise)
], InstaProfilesController.prototype, "updateProfile", null);
__decorate([
    (0, common_1.Delete)(':id'),
    (0, common_1.HttpCode)(common_1.HttpStatus.NO_CONTENT),
    (0, swagger_1.ApiOperation)({ summary: 'Delete an Instagram profile by ID.' }),
    (0, swagger_1.ApiParam)({
        name: 'id',
        description: 'UUID of the profile to delete',
        type: String,
        format: 'uuid',
    }),
    (0, swagger_1.ApiResponse)({ status: 204, description: 'Profile deleted successfully.' }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'Profile not found.' }),
    __param(0, (0, common_1.Param)('id', common_1.ParseUUIDPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], InstaProfilesController.prototype, "deleteProfile", null);
exports.InstaProfilesController = InstaProfilesController = InstaProfilesController_1 = __decorate([
    (0, swagger_1.ApiTags)('Instagram Profiles'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('profiles/instagram'),
    __metadata("design:paramtypes", [insta_profiles_service_1.InstaProfilesService])
], InstaProfilesController);
//# sourceMappingURL=insta-profiles.controller.js.map