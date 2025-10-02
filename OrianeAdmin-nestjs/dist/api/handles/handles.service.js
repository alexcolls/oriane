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
var HandlesService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.HandlesService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const Papa = require("papaparse");
const oriane_user_entity_1 = require("../../entities/oriane-user.entity");
const insta_profiles_entity_1 = require("../../entities/insta-profiles.entity");
const content_entity_1 = require("../../entities/content.entity");
const typeorm_filters_util_1 = require("../../utils/typeorm-filters.util");
const aws_sqs_service_1 = require("../../aws/aws.sqs.service");
const aws_module_1 = require("../../aws/aws.module");
let HandlesService = HandlesService_1 = class HandlesService {
    constructor(orianeUserRepository, instaProfileRepository, instaContentRepository, sqsHandlesService) {
        this.orianeUserRepository = orianeUserRepository;
        this.instaProfileRepository = instaProfileRepository;
        this.instaContentRepository = instaContentRepository;
        this.sqsHandlesService = sqsHandlesService;
        this.logger = new common_1.Logger(HandlesService_1.name);
    }
    getNextMonthStart() {
        const now = new Date();
        return new Date(now.getFullYear(), now.getMonth() + 1, 1);
    }
    async uploadCSV(file) {
        this.logger.log(`Received file in service: ${file ? file.originalname : 'No file'}`);
        if (!file || !file.buffer) {
            throw new common_1.BadRequestException('No file uploaded or file buffer is missing.');
        }
        this.logger.log(`Processing file: ${file.originalname}, size: ${file.size} bytes.`);
        const fileContent = file.buffer.toString('utf-8');
        return new Promise((resolve, reject) => {
            Papa.parse(fileContent, {
                header: true,
                skipEmptyLines: true,
                complete: (results) => {
                    this.logger.log(`CSV parsed successfully. Rows found: ${results.data.length}`);
                    if (results.errors && results.errors.length > 0) {
                        this.logger.warn(`CSV parsed with ${results.errors.length} row-level error(s):`);
                        results.errors.forEach((err) => {
                            this.logger.warn(`Row ${err.row}: [${err.code}] ${err.message}`);
                        });
                    }
                    const usernames = results.data
                        .map((row) => row && row['Account'])
                        .filter((u) => typeof u === 'string' && u.trim() !== '');
                    this.logger.log(`Extracted usernames: ${usernames.join(', ')} (Count: ${usernames.length})`);
                    if (usernames.length === 0) {
                        this.logger.warn('No valid usernames extracted from the CSV.');
                        resolve({
                            success: true,
                            message: 'CSV processed, but no valid usernames were found to process.',
                        });
                        return;
                    }
                    this.logger.log(`Starting processing of ${usernames.length} usernames via SQS`);
                    this.processUsernamesViaSqs(usernames)
                        .then(() => {
                        resolve({
                            success: true,
                            message: `CSV received with ${usernames.length} usernames. Messages sent to SQS for processing.`,
                        });
                    })
                        .catch((error) => {
                        this.logger.error(`Error processing usernames via SQS: ${error.message}`, error.stack);
                        resolve({
                            success: false,
                            message: `CSV received but failed to send to SQS: ${error.message}`,
                        });
                    });
                },
                error: (err) => {
                    this.logger.error(`Fatal CSV parsing error: ${err.message}`, err.stack);
                    reject(new common_1.InternalServerErrorException(`Error parsing CSV: ${err.message || 'Unknown parsing error.'}`));
                },
            });
        });
    }
    async processUsernamesViaSqs(usernames) {
        this.logger.log(`Starting processUsernamesViaSqs with ${usernames.length} usernames`);
        this.logger.log(`First 5 usernames: ${usernames.slice(0, 5).join(', ')}`);
        const validUsernames = usernames
            .filter((username) => username && typeof username === 'string' && username.trim() !== '')
            .map((username) => username.trim());
        if (validUsernames.length === 0) {
            this.logger.warn('No valid usernames to process');
            return;
        }
        try {
            if (!this.sqsHandlesService) {
                this.logger.error('SQS Handles Service is not available');
                throw new Error('SQS Handles Service is not available');
            }
            const messagePayload = {
                usernames: validUsernames,
            };
            this.logger.log(`Sending SQS message with ${validUsernames.length} usernames:`, JSON.stringify(messagePayload, null, 2));
            await this.sqsHandlesService.sendMessage(messagePayload);
            this.logger.log(`Successfully sent ${validUsernames.length} usernames to SQS handles queue`);
        }
        catch (error) {
            this.logger.error(`Error sending usernames to SQS: ${error.message || error}`, error.stack);
            this.logger.error(`SQS Service available: ${!!this.sqsHandlesService}`);
            throw error;
        }
    }
    async testSqsConnection() {
        this.logger.log('Testing SQS connection...');
        if (!this.sqsHandlesService) {
            throw new Error('SQS Handles Service is not available');
        }
        const testMessage = {
            test: true,
            timestamp: new Date().toISOString(),
            message: 'SQS connection test'
        };
        this.logger.log('Sending test message to SQS...');
        await this.sqsHandlesService.sendMessage(testMessage);
        this.logger.log('Test message sent successfully');
    }
    async addWatchedHandleInternal(username) {
        const payload = {
            username,
            checkFrequency: 43200,
            priority: 'medium',
            isWatched: true,
            isDeactivated: false,
            stateError: false,
            accountStatus: 'Pending',
            errorMessage: null,
            environment: 'default',
            lastChecked: null,
            lastCursor: null,
            nextCheckAt: this.getNextMonthStart(),
            createdAt: new Date(),
            firstFetched: null,
        };
        const newUser = this.orianeUserRepository.create(payload);
        return this.orianeUserRepository.save(newUser);
    }
    async addUser(username, priority, environment) {
        this.logger.log(`Adding handle: ${username}, Priority: ${priority}, Env: ${environment || 'default'}`);
        if (!username) {
            throw new common_1.BadRequestException('Username is required.');
        }
        if (!['low', 'medium', 'high'].includes(priority.toLowerCase())) {
            throw new common_1.BadRequestException("Invalid priority value. Must be 'low', 'medium', or 'high'.");
        }
        const existingUser = await this.orianeUserRepository.findOneBy({
            username,
        });
        if (existingUser) {
            this.logger.warn(`Username '${username}' already exists.`);
            throw new common_1.ConflictException(`The username '${username}' already exists in the database.`);
        }
        const payload = {
            username,
            checkFrequency: 43200,
            priority: priority.toLowerCase(),
            isCreator: true,
            isWatched: false,
            isDeactivated: false,
            stateError: false,
            accountStatus: 'Pending',
            errorMessage: null,
            environment: environment || 'default',
            lastChecked: null,
            lastCursor: null,
            nextCheckAt: new Date(),
            firstFetched: null,
        };
        try {
            const newUser = this.orianeUserRepository.create(payload);
            const savedUser = await this.orianeUserRepository.save(newUser);
            this.logger.log(`User '${username}' added. Profile collection will be scheduled.`);
            return {
                message: `User '${username}' has been successfully added. Profile collection will be scheduled.`,
                data: savedUser,
            };
        }
        catch (error) {
            this.logger.error(`Failed to save handle '${username}': ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException(`Failed to save handle: ${error.message}`);
        }
    }
    async addWatchedHandle(username) {
        if (!username) {
            throw new common_1.BadRequestException('Username is required.');
        }
        const trimmedUsername = username.trim();
        const existingUser = await this.orianeUserRepository.findOneBy({
            username: trimmedUsername,
        });
        if (existingUser) {
            this.logger.warn(`Username '${trimmedUsername}' already exists.`);
            throw new common_1.ConflictException(`The username '${trimmedUsername}' already exists in the database.`);
        }
        try {
            const newUser = await this.addWatchedHandleInternal(trimmedUsername);
            this.logger.log(`Username '${trimmedUsername}' successfully added to database`);
            return {
                message: `Username '${trimmedUsername}' has been successfully added to the watchlist.`,
                data: newUser,
            };
        }
        catch (error) {
            this.logger.error(`Error adding username '${trimmedUsername}' to database: ${error.message || error}`, error.stack);
            throw new common_1.InternalServerErrorException(`Failed to add username '${trimmedUsername}' to database`);
        }
    }
    async updateHandle(currentUsername, updates) {
        const userToUpdate = await this.orianeUserRepository.findOneBy({
            username: currentUsername,
        });
        if (!userToUpdate) {
            throw new common_1.NotFoundException(`User with username ${currentUsername} not found.`);
        }
        try {
            const deleteResult = await this.instaProfileRepository.delete({
                username: currentUsername,
            });
            this.logger.log(`Deleted ${deleteResult.affected} rows from insta_profiles for username ${currentUsername}.`);
        }
        catch (error) {
            this.logger.error(`Failed to delete associated profile in insta_profiles for ${currentUsername}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException(`Failed to delete associated profile: ${error.message}`);
        }
        const updatedDataPayload = {
            ...updates,
            stateError: false,
            errorMessage: null,
        };
        if (updates.username && updates.username !== currentUsername) {
            const existingUserWithNewUsername = await this.orianeUserRepository.findOneBy({
                username: updates.username,
            });
            if (existingUserWithNewUsername) {
                throw new common_1.ConflictException(`The new username '${updates.username}' is already taken.`);
            }
        }
        this.orianeUserRepository.merge(userToUpdate, updatedDataPayload);
        try {
            const updatedUser = await this.orianeUserRepository.save(userToUpdate);
            return {
                message: 'User updated successfully.',
                updatedUser,
            };
        }
        catch (error) {
            this.logger.error(`Failed to update user ${currentUsername}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException(`Failed to update user: ${error.message}`);
        }
    }
    async deactivateHandle(username) {
        const user = await this.orianeUserRepository.findOneBy({ username });
        if (!user) {
            throw new common_1.NotFoundException(`User with username ${username} not found.`);
        }
        user.isDeactivated = true;
        user.nextCheckAt = null;
        user.lastCursor = new Date();
        try {
            return await this.orianeUserRepository.save(user);
        }
        catch (error) {
            this.logger.error(`Failed to deactivate handle ${username}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to deactivate handle.');
        }
    }
    async activateHandle(username) {
        const user = await this.orianeUserRepository.findOneBy({ username });
        if (!user) {
            throw new common_1.NotFoundException(`User with username ${username} not found.`);
        }
        user.isDeactivated = false;
        user.nextCheckAt = this.getNextMonthStart();
        user.lastCursor = null;
        try {
            return await this.orianeUserRepository.save(user);
        }
        catch (error) {
            this.logger.error(`Failed to activate handle ${username}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to activate handle.');
        }
    }
    async getHandleByUsername(username) {
        const user = await this.orianeUserRepository.findOneBy({ username });
        if (!user) {
            throw new common_1.NotFoundException(`User with username '${username}' not found.`);
        }
        return user;
    }
    async getHandles(environment, user_type, offset, limit, search, filters) {
        const entityAlias = 'orianeUser';
        const queryBuilder = this.orianeUserRepository.createQueryBuilder(entityAlias);
        if (environment && environment.trim() !== '') {
            queryBuilder.where(`${entityAlias}.environment = :environment`, {
                environment,
            });
        }
        if (user_type === 'users') {
            queryBuilder.andWhere(`${entityAlias}.isCreator = :isCreator`, {
                isCreator: true,
            });
        }
        else if (user_type === 'watched') {
            queryBuilder.andWhere(`${entityAlias}.isWatched = :isWatched`, {
                isWatched: true,
            });
        }
        if (search) {
            const matchingInstaProfiles = await this.instaProfileRepository
                .createQueryBuilder('profile')
                .select('profile.orianeUserId')
                .where('profile.username ILIKE :search', { search: `%${search}%` })
                .andWhere('profile.orianeUserId IS NOT NULL')
                .getRawMany();
            this.logger.log(`Search for "${search}" found ${matchingInstaProfiles.length} matching insta_profiles`);
            const matchingOrianeUserIds = matchingInstaProfiles.map((p) => p.profile_orianeUserId);
            if (matchingOrianeUserIds.length > 0) {
                this.logger.log(`Found matching OrianeUser IDs: ${matchingOrianeUserIds.join(', ')}`);
                queryBuilder.andWhere(`(${entityAlias}.username ILIKE :search OR ${entityAlias}.id IN (:...matchingIds))`, {
                    search: `%${search}%`,
                    matchingIds: matchingOrianeUserIds,
                });
            }
            else {
                this.logger.log(`No matching insta_profiles found, searching only in oriane_users.username`);
                queryBuilder.andWhere(`${entityAlias}.username ILIKE :search`, {
                    search: `%${search}%`,
                });
            }
        }
        (0, typeorm_filters_util_1.applyTypeOrmFilters)(queryBuilder, entityAlias, filters);
        try {
            const [data, total] = await queryBuilder
                .orderBy(`${entityAlias}.createdAt`, 'DESC')
                .skip(offset)
                .take(limit)
                .getManyAndCount();
            return { data, total };
        }
        catch (error) {
            this.logger.error(`Error fetching handles: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve handles.');
        }
    }
    async getVideoCodesByUsername(user_type, offset, limit, search) {
        const whereConditionsInstaContent = {};
        if (user_type === 'users') {
            whereConditionsInstaContent.isMonitored = true;
        }
        else if (user_type === 'watched') {
            whereConditionsInstaContent.isWatched = true;
        }
        const distinctUsernamesQb = this.instaContentRepository
            .createQueryBuilder('content')
            .select('DISTINCT content.username', 'username')
            .where(whereConditionsInstaContent);
        if (search) {
            distinctUsernamesQb.andWhere('content.username ILIKE :search', {
                search: `%${search}%`,
            });
        }
        const totalUsernameGroups = await distinctUsernamesQb.getCount();
        const pagedUsernamesResult = await distinctUsernamesQb
            .orderBy('username', 'ASC')
            .skip(offset)
            .limit(limit)
            .getRawMany();
        const pagedUsernames = pagedUsernamesResult.map((u) => u.username);
        if (pagedUsernames.length === 0) {
            return { data: [], total: totalUsernameGroups };
        }
        const videosData = await this.instaContentRepository.find({
            select: ['username', 'code'],
            where: {
                ...whereConditionsInstaContent,
                username: (0, typeorm_2.In)(pagedUsernames),
            },
            order: { username: 'ASC', createdAt: 'DESC' },
        });
        const groupedVideos = {};
        videosData.forEach((video) => {
            if (!groupedVideos[video.username]) {
                groupedVideos[video.username] = {
                    username: video.username,
                    video_codes: [],
                };
            }
            groupedVideos[video.username].video_codes.push(video.code);
        });
        return {
            data: Object.values(groupedVideos),
            total: totalUsernameGroups,
        };
    }
    async getAllVideoCodes(user_type) {
        const whereConditions = {
            code: (0, typeorm_2.Not)((0, typeorm_2.IsNull)()),
        };
        if (user_type === 'users') {
            whereConditions.isMonitored = true;
        }
        else if (user_type === 'watched') {
            whereConditions.isWatched = true;
        }
        try {
            const videosData = await this.instaContentRepository.find({
                select: ['code'],
                where: whereConditions,
            });
            return videosData.map(({ code }) => code);
        }
        catch (error) {
            this.logger.error(`Error fetching all video codes for type ${user_type}: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException('Failed to retrieve all video codes.');
        }
    }
};
exports.HandlesService = HandlesService;
exports.HandlesService = HandlesService = HandlesService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(oriane_user_entity_1.OrianeUser)),
    __param(1, (0, typeorm_1.InjectRepository)(insta_profiles_entity_1.InstaProfile)),
    __param(2, (0, typeorm_1.InjectRepository)(content_entity_1.InstaContent)),
    __param(3, (0, common_1.Inject)(aws_module_1.SQS_INSTAGRAM_HANDLES_SERVICE)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        aws_sqs_service_1.AwsSqsService])
], HandlesService);
//# sourceMappingURL=handles.service.js.map