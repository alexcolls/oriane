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
var InstaProfilesService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.InstaProfilesService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const insta_profiles_entity_1 = require("../../../entities/insta-profiles.entity");
let InstaProfilesService = InstaProfilesService_1 = class InstaProfilesService {
    constructor(instaProfileRepository) {
        this.instaProfileRepository = instaProfileRepository;
        this.logger = new common_1.Logger(InstaProfilesService_1.name);
    }
    async getAllProfiles(isCreator) {
        try {
            const whereConditions = {};
            if (isCreator !== undefined) {
                this.logger.warn("Filtering by 'isCreator' in getAllProfiles, ensure 'InstaProfile' entity has this field or use a join if it's on a related entity.");
            }
            return await this.instaProfileRepository.find({ where: whereConditions });
        }
        catch (error) {
            this.logger.error(`Error fetching all profiles: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve profiles.');
        }
    }
    async getProfileByUsername(username) {
        try {
            const profile = await this.instaProfileRepository.findOneBy({ username });
            if (!profile) {
                throw new common_1.NotFoundException(`Profile with username '${username}' not found.`);
            }
            return profile;
        }
        catch (error) {
            if (error instanceof common_1.NotFoundException)
                throw error;
            this.logger.error(`Error fetching profile by username ${username}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve profile by username.');
        }
    }
    async getProfileById(id) {
        try {
            const profile = await this.instaProfileRepository.findOneBy({ id });
            if (!profile) {
                throw new common_1.NotFoundException(`Profile with ID '${id}' not found.`);
            }
            return profile;
        }
        catch (error) {
            if (error instanceof common_1.NotFoundException)
                throw error;
            this.logger.error(`Error fetching profile by ID ${id}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve profile by ID.');
        }
    }
    async createProfile(profileData) {
        try {
            const newProfileEntity = this.instaProfileRepository.create(profileData);
            return await this.instaProfileRepository.save(newProfileEntity);
        }
        catch (error) {
            if (error.code === '23505') {
                this.logger.warn(`Attempted to create a profile with an already existing unique field (e.g. username): ${error.detail || error.message}`);
                throw new common_1.ConflictException('Profile with this username or other unique field already exists.');
            }
            this.logger.error(`Error creating profile: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to create profile.');
        }
    }
    async updateProfile(id, profileUpdateData) {
        const profileToUpdate = await this.instaProfileRepository.preload({
            id: id,
            ...profileUpdateData,
        });
        if (!profileToUpdate) {
            throw new common_1.NotFoundException(`Profile with ID '${id}' not found for update.`);
        }
        try {
            return await this.instaProfileRepository.save(profileToUpdate);
        }
        catch (error) {
            if (error.code === '23505') {
                this.logger.warn(`Attempted to update profile ${id} with an already existing unique field: ${error.detail || error.message}`);
                throw new common_1.ConflictException('Cannot update profile, a unique field conflict occurred (e.g. username already taken).');
            }
            this.logger.error(`Error updating profile ${id}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to update profile.');
        }
    }
    async deleteProfile(id) {
        try {
            const result = await this.instaProfileRepository.delete(id);
            if (result.affected === 0) {
                throw new common_1.NotFoundException(`Profile with ID '${id}' not found for deletion.`);
            }
        }
        catch (error) {
            this.logger.error(`Error deleting profile ${id}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to delete profile.');
        }
    }
};
exports.InstaProfilesService = InstaProfilesService;
exports.InstaProfilesService = InstaProfilesService = InstaProfilesService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(insta_profiles_entity_1.InstaProfile)),
    __metadata("design:paramtypes", [typeorm_2.Repository])
], InstaProfilesService);
//# sourceMappingURL=insta-profiles.service.js.map