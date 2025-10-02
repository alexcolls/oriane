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
var ProfileCollectorService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProfileCollectorService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const hiker_api_client_service_1 = require("../../../api/hiker-api-client/hiker-api-client.service");
const insta_profiles_entity_1 = require("../../../entities/insta-profiles.entity");
const oriane_user_entity_1 = require("../../../entities/oriane-user.entity");
let ProfileCollectorService = ProfileCollectorService_1 = class ProfileCollectorService {
    constructor(hikerApiClient, instaProfileRepository, orianeUserRepository) {
        this.hikerApiClient = hikerApiClient;
        this.instaProfileRepository = instaProfileRepository;
        this.orianeUserRepository = orianeUserRepository;
        this.logger = new common_1.Logger(ProfileCollectorService_1.name);
    }
    async collectProfile(username) {
        this.logger.log(`Starting profile collection for username: ${username}`);
        try {
            const hikerProfileResponse = await this.hikerApiClient.getUserByUsername(username);
            const externalUserProfile = hikerProfileResponse?.user;
            if (!externalUserProfile) {
                this.logger.warn(`Hiker API did not return a user profile for username: ${username}`);
                throw new common_1.NotFoundException(`User profile not found via Hiker API for username: ${username}`);
            }
            const relatedOrianeUser = await this.orianeUserRepository.findOne({
                where: { username: username },
                select: ['id'],
            });
            if (!relatedOrianeUser) {
                this.logger.warn(`No corresponding OrianeUser found for username: ${username} to link InstaProfile.`);
                throw new common_1.NotFoundException(`Related OrianeUser (internal record) not found for username: ${username}. Cannot save InstaProfile.`);
            }
            const profilePicUrl = externalUserProfile.profile_pic_url_hd ||
                externalUserProfile.profile_pic_url;
            const profilePayload = {
                userId: externalUserProfile.pk,
                username: externalUserProfile.username,
                fullName: externalUserProfile.full_name,
                biography: externalUserProfile.biography,
                followersCount: externalUserProfile.follower_count,
                followingCount: externalUserProfile.following_count,
                mediaCount: externalUserProfile.media_count,
                isVerified: externalUserProfile.is_verified,
                isPrivate: externalUserProfile.is_private,
                profilePic: profilePicUrl,
                publicEmail: externalUserProfile.public_email,
                externalUrl: externalUserProfile.external_url,
                orianeUserId: relatedOrianeUser.id,
                platform: 'Instagram',
                accountType: externalUserProfile.account_type,
                isBusinessAccount: externalUserProfile.is_business,
                category: externalUserProfile.category,
                averageLikes: externalUserProfile.average_like_count,
                averageComments: externalUserProfile.average_comment_count,
                lastUpdated: new Date(),
            };
            Object.keys(profilePayload).forEach((key) => profilePayload[key] === undefined &&
                delete profilePayload[key]);
            await this.instaProfileRepository.upsert(profilePayload, {
                conflictPaths: ['userId'],
                skipUpdateIfNoValuesChanged: true,
            });
            this.logger.log(`Profile for ${username} (Insta User ID: ${externalUserProfile.pk}) saved/updated successfully in insta_profiles.`);
            return true;
        }
        catch (error) {
            this.logger.error(`Error collecting profile for ${username}: ${error.message}`, error.stack);
            if (error instanceof common_1.HttpException) {
                throw error;
            }
            throw new common_1.InternalServerErrorException(`Failed to process profile for ${username}: ${error.message}`);
        }
    }
};
exports.ProfileCollectorService = ProfileCollectorService;
exports.ProfileCollectorService = ProfileCollectorService = ProfileCollectorService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(1, (0, typeorm_1.InjectRepository)(insta_profiles_entity_1.InstaProfile)),
    __param(2, (0, typeorm_1.InjectRepository)(oriane_user_entity_1.OrianeUser)),
    __metadata("design:paramtypes", [hiker_api_client_service_1.HikerApiClientService,
        typeorm_2.Repository,
        typeorm_2.Repository])
], ProfileCollectorService);
//# sourceMappingURL=profile-collector.service.js.map