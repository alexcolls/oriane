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
var SearchAccountsJobProcessor_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.SearchAccountsJobProcessor = void 0;
const common_1 = require("@nestjs/common");
const schedule_1 = require("@nestjs/schedule");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const hiker_api_client_service_1 = require("../hiker-api-client/hiker-api-client.service");
const search_account_job_entity_1 = require("../../entities/search-account-job.entity");
const search_account_result_entity_1 = require("../../entities/search-account-result.entity");
let SearchAccountsJobProcessor = SearchAccountsJobProcessor_1 = class SearchAccountsJobProcessor {
    constructor(searchJobRepository, searchResultRepository, hikerApiService) {
        this.searchJobRepository = searchJobRepository;
        this.searchResultRepository = searchResultRepository;
        this.hikerApiService = hikerApiService;
        this.logger = new common_1.Logger(SearchAccountsJobProcessor_1.name);
        this.DAYS_THRESHOLD = 30;
    }
    async processPendingJobs() {
        const pendingJobs = await this.searchJobRepository.find({
            where: { status: search_account_job_entity_1.SearchAccountJobStatus.PENDING },
            order: { createdAt: 'ASC' },
            take: 1,
            select: [
                'id',
                'keywords',
                'totalKeywords',
                'processedKeywords',
                'totalFoundAccounts',
                'filteredAccounts',
                'status',
                'createdAt',
                'startedAt',
                'completedAt',
                'csvFileUrl',
                'errorMessage',
            ],
        });
        if (pendingJobs.length === 0) {
            return;
        }
        const searchJob = pendingJobs[0];
        this.logger.log(`Processing job ${searchJob.id} with ${searchJob.keywords.length} keywords`);
        const jobId = searchJob.id;
        const keywords = searchJob.keywords;
        let jobData;
        try {
            const jobWithData = await this.searchJobRepository.findOne({
                where: { id: jobId },
                select: ['jobData'],
            });
            jobData = jobWithData?.jobData;
        }
        catch {
            this.logger.warn('Could not fetch jobData, using default filter values');
        }
        const resultsPerKeyword = jobData?.resultsPerKeyword || 100;
        const minFollowerCount = jobData?.minFollowerCount || 10000;
        const maxFollowerCount = jobData?.maxFollowerCount || null;
        const includePrivateAccounts = jobData?.includePrivateAccounts || false;
        const minMediaCount = jobData?.minMediaCount || 0;
        const requireVerified = jobData?.requireVerified || false;
        const requireBusiness = jobData?.requireBusiness || false;
        this.logger.log(`Starting bulk search job ${jobId} with ${keywords.length} keywords`);
        await this.updateJobStatus(jobId, search_account_job_entity_1.SearchAccountJobStatus.PROCESSING, new Date());
        try {
            let processedKeywords = 0;
            let totalFoundAccounts = 0;
            let totalFilteredAccounts = 0;
            for (const keyword of keywords) {
                this.logger.log(`Processing keyword: ${keyword} (${processedKeywords + 1}/${keywords.length})`);
                try {
                    const searchResults = await this.hikerApiService.searchAccountsV2(keyword, resultsPerKeyword);
                    if (!searchResults?.users) {
                        this.logger.warn(`No results found for keyword: ${keyword}`);
                        continue;
                    }
                    totalFoundAccounts += searchResults.users.length;
                    const batchSize = 5;
                    const users = searchResults.users;
                    for (let i = 0; i < users.length; i += batchSize) {
                        const batch = users.slice(i, i + batchSize);
                        const batchPromises = batch.map(async (user) => {
                            try {
                                const detailedProfile = await this.hikerApiService.getUserByUsername(user.username);
                                if (!detailedProfile?.user) {
                                    this.logger.warn(`Could not fetch profile for user: ${user.username}`);
                                    return { success: false, filtered: false };
                                }
                                const profileUser = detailedProfile.user;
                                const accountResult = new search_account_result_entity_1.SearchAccountResult();
                                accountResult.jobId = jobId;
                                accountResult.keyword = keyword;
                                accountResult.username = profileUser.username;
                                accountResult.userPk = profileUser.pk;
                                accountResult.fullName = profileUser.full_name || '';
                                accountResult.isPrivate = profileUser.is_private;
                                accountResult.profilePicUrl = profileUser.profile_pic_url;
                                accountResult.isVerified = profileUser.is_verified;
                                accountResult.mediaCount = profileUser.media_count || 0;
                                accountResult.followerCount = profileUser.follower_count || 0;
                                accountResult.followingCount = profileUser.following_count || 0;
                                accountResult.biography = profileUser.biography || '';
                                accountResult.externalUrl = profileUser.external_url || '';
                                accountResult.accountType = profileUser.account_type || '';
                                accountResult.isBusiness = profileUser.is_business || false;
                                accountResult.category = profileUser.category || '';
                                const filterResult = await this.applyFilters(profileUser, {
                                    minFollowerCount,
                                    maxFollowerCount,
                                    includePrivateAccounts,
                                    minMediaCount,
                                    requireVerified,
                                    requireBusiness,
                                });
                                accountResult.passedFilter = filterResult.passed;
                                accountResult.filterReason = filterResult.reason;
                                await this.searchResultRepository.save(accountResult);
                                return { success: true, filtered: filterResult.passed };
                            }
                            catch (error) {
                                this.logger.error(`Error processing user ${user.username}: ${error.message}`);
                                return { success: false, filtered: false };
                            }
                        });
                        const batchResults = await Promise.all(batchPromises);
                        batchResults.forEach((result) => {
                            if (result.success && result.filtered) {
                                totalFilteredAccounts++;
                            }
                        });
                        await this.sleep(200);
                    }
                }
                catch (error) {
                    this.logger.error(`Error processing keyword ${keyword}: ${error.message}`);
                }
                processedKeywords++;
                await this.updateJobProgress(jobId, processedKeywords, totalFoundAccounts, totalFilteredAccounts);
                await this.sleep(200);
            }
            await this.completeJob(jobId, null, totalFoundAccounts, totalFilteredAccounts);
            this.logger.log(`Bulk search job ${jobId} completed successfully. Found ${totalFilteredAccounts} filtered accounts out of ${totalFoundAccounts} total.`);
        }
        catch (error) {
            this.logger.error(`Bulk search job ${jobId} failed: ${error.message}`, error.stack);
            await this.failJob(jobId, error.message);
            throw error;
        }
    }
    async applyFilters(user, filters) {
        const { minFollowerCount, maxFollowerCount, includePrivateAccounts, minMediaCount, requireVerified, requireBusiness, } = filters;
        if (user.is_private && !includePrivateAccounts) {
            return { passed: false, reason: 'Account is private' };
        }
        const followerCount = user.follower_count || 0;
        if (followerCount < minFollowerCount) {
            return {
                passed: false,
                reason: `Follower count ${followerCount} below minimum ${minFollowerCount}`,
            };
        }
        if (maxFollowerCount && followerCount > maxFollowerCount) {
            return {
                passed: false,
                reason: `Follower count ${followerCount} above maximum ${maxFollowerCount}`,
            };
        }
        if (minMediaCount > 0) {
            try {
                const recentMediaCount = await this.getRecentMediaCount(user.pk);
                if (recentMediaCount < minMediaCount) {
                    return {
                        passed: false,
                        reason: `Only ${recentMediaCount} posts in last 30 days, below minimum ${minMediaCount}`,
                    };
                }
            }
            catch {
                const totalMediaCount = user.media_count || 0;
                if (totalMediaCount < minMediaCount) {
                    return {
                        passed: false,
                        reason: `Could not verify recent activity, total media count ${totalMediaCount} below minimum ${minMediaCount}`,
                    };
                }
            }
        }
        if (requireVerified && !user.is_verified) {
            return { passed: false, reason: 'Account is not verified' };
        }
        if (requireBusiness && !user.is_business) {
            return { passed: false, reason: 'Account is not a business account' };
        }
        return { passed: true };
    }
    async getRecentMediaCount(userId) {
        try {
            const mediaResponse = await this.hikerApiService.getUserMedias(userId);
            if (!mediaResponse?.items || !Array.isArray(mediaResponse.items)) {
                return 0;
            }
            const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
            const recentMedia = mediaResponse.items.filter((media) => {
                const mediaTimestamp = media.taken_at ? media.taken_at * 1000 : 0;
                return mediaTimestamp >= thirtyDaysAgo;
            });
            return recentMedia.length;
        }
        catch (error) {
            this.logger.warn(`Could not fetch recent media for user ${userId}: ${error.message}`);
            throw error;
        }
    }
    async updateJobStatus(jobId, status, timestamp) {
        const updateData = { status };
        if (status === search_account_job_entity_1.SearchAccountJobStatus.PROCESSING) {
            updateData.startedAt = timestamp || new Date();
        }
        else if (status === search_account_job_entity_1.SearchAccountJobStatus.COMPLETED) {
            updateData.completedAt = timestamp || new Date();
        }
        await this.searchJobRepository.update(jobId, updateData);
    }
    async updateJobProgress(jobId, processedKeywords, totalFoundAccounts, filteredAccounts) {
        await this.searchJobRepository.update(jobId, {
            processedKeywords,
            totalFoundAccounts,
            filteredAccounts,
        });
    }
    async completeJob(jobId, csvFileUrl, totalFoundAccounts, filteredAccounts) {
        await this.searchJobRepository.update(jobId, {
            status: search_account_job_entity_1.SearchAccountJobStatus.COMPLETED,
            completedAt: new Date(),
            csvFileUrl,
            totalFoundAccounts,
            filteredAccounts,
        });
    }
    async failJob(jobId, errorMessage) {
        await this.searchJobRepository.update(jobId, {
            status: search_account_job_entity_1.SearchAccountJobStatus.FAILED,
            errorMessage,
        });
    }
    sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
};
exports.SearchAccountsJobProcessor = SearchAccountsJobProcessor;
__decorate([
    (0, schedule_1.Cron)(schedule_1.CronExpression.EVERY_30_SECONDS),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], SearchAccountsJobProcessor.prototype, "processPendingJobs", null);
exports.SearchAccountsJobProcessor = SearchAccountsJobProcessor = SearchAccountsJobProcessor_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(search_account_job_entity_1.SearchAccountJob)),
    __param(1, (0, typeorm_1.InjectRepository)(search_account_result_entity_1.SearchAccountResult)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        typeorm_2.Repository,
        hiker_api_client_service_1.HikerApiClientService])
], SearchAccountsJobProcessor);
//# sourceMappingURL=search-accounts-job.processor.js.map