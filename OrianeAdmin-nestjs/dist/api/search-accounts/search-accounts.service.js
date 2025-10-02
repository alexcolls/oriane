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
var SearchAccountsService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.SearchAccountsService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const common_2 = require("@nestjs/common");
const aws_sqs_service_1 = require("../../aws/aws.sqs.service");
const aws_module_1 = require("../../aws/aws.module");
const hiker_api_client_service_1 = require("../hiker-api-client/hiker-api-client.service");
const search_account_job_entity_1 = require("../../entities/search-account-job.entity");
const search_account_result_entity_1 = require("../../entities/search-account-result.entity");
const csv = require("csv-parser");
const stream_1 = require("stream");
let SearchAccountsService = SearchAccountsService_1 = class SearchAccountsService {
    constructor(hikerApiService, searchJobRepository, searchResultRepository, searchSqsService) {
        this.hikerApiService = hikerApiService;
        this.searchJobRepository = searchJobRepository;
        this.searchResultRepository = searchResultRepository;
        this.searchSqsService = searchSqsService;
        this.logger = new common_1.Logger(SearchAccountsService_1.name);
    }
    async searchAccountsByKeyword(dto) {
        this.logger.log(`Searching for accounts with keyword: ${dto.keyword}`);
        try {
            const response = await this.hikerApiService.searchAccountsV2(dto.keyword, dto.count);
            if (!response || !response.users) {
                this.logger.warn(`No users found for keyword: ${dto.keyword}`);
                return [];
            }
            this.logger.log(`Found ${response.users.length} accounts for keyword: ${dto.keyword}`);
            return response.users.map((user) => ({
                user: {
                    pk: user.pk,
                    username: user.username,
                    full_name: user.full_name,
                    is_private: user.is_private,
                    profile_pic_url: user.profile_pic_url,
                    is_verified: user.is_verified,
                    media_count: user.media_count,
                    follower_count: user.follower_count,
                    following_count: user.following_count,
                    biography: user.biography,
                    external_url: user.external_url,
                    account_type: user.account_type,
                    is_business: user.is_business,
                    category: user.category,
                },
            }));
        }
        catch (error) {
            this.logger.error(`Error searching accounts for keyword ${dto.keyword}: ${error.message}`);
            throw new common_1.InternalServerErrorException(`Failed to search accounts for keyword: ${dto.keyword}`);
        }
    }
    async startBulkSearch(dto) {
        this.logger.log(`Starting bulk search for ${dto.keywords.length} keywords`);
        try {
            const searchJob = new search_account_job_entity_1.SearchAccountJob();
            searchJob.keywords = dto.keywords;
            searchJob.totalKeywords = dto.keywords.length;
            searchJob.status = search_account_job_entity_1.SearchAccountJobStatus.PENDING;
            searchJob.processedKeywords = 0;
            searchJob.totalFoundAccounts = 0;
            searchJob.filteredAccounts = 0;
            const jobParams = {
                resultsPerKeyword: dto.resultsPerKeyword || 100,
                minFollowerCount: dto.minFollowers || 10000,
                maxFollowerCount: dto.maxFollowers,
                includePrivateAccounts: dto.includePrivateAccounts || false,
                minMediaCount: dto.minPostsInLastMonth || 1,
                requireVerified: dto.requireVerified || false,
                requireBusiness: dto.requireBusiness || false,
            };
            try {
                searchJob.jobData = jobParams;
            }
            catch {
                this.logger.warn('jobData column does not exist yet, using default filter values');
            }
            this.logger.log(`Saving job to database...`);
            const savedJob = (await Promise.race([
                this.searchJobRepository.save(searchJob),
                new Promise((_, reject) => setTimeout(() => reject(new Error('Database save timeout')), 10000)),
            ]));
            const jobData = {
                jobId: savedJob.id,
                keywords: dto.keywords,
                resultsPerKeyword: dto.resultsPerKeyword || 100,
                minFollowerCount: dto.minFollowers || 10000,
                maxFollowerCount: dto.maxFollowers,
                includePrivateAccounts: dto.includePrivateAccounts || false,
                minMediaCount: dto.minPostsInLastMonth || 1,
                requireVerified: dto.requireVerified || false,
                requireBusiness: dto.requireBusiness || false,
            };
            this.logger.log(`Sending job to SQS queue...`);
            await Promise.race([
                this.searchSqsService.sendMessage(jobData),
                new Promise((_, reject) => setTimeout(() => reject(new Error('SQS send timeout')), 10000)),
            ]);
            const estimatedTimeMinutes = Math.ceil((dto.keywords.length * 2) / 60);
            return {
                searchAccountsId: savedJob.id,
                status: search_account_job_entity_1.SearchAccountJobStatus.PENDING,
                totalKeywords: dto.keywords.length,
                estimatedTimeMinutes,
                message: 'Bulk search job started successfully',
            };
        }
        catch (error) {
            this.logger.error(`Error starting bulk search: ${error.message}`, error.stack);
            if (error.message === 'Database save timeout') {
                throw new common_1.InternalServerErrorException('Database connection timeout. Please try again.');
            }
            else if (error.message === 'SQS send timeout') {
                throw new common_1.InternalServerErrorException('SQS queue connection timeout. Please try again.');
            }
            throw new common_1.InternalServerErrorException(`Failed to start bulk search job: ${error.message}`);
        }
    }
    async startCsvSearch(file, dto) {
        this.logger.log(`Starting CSV search with file: ${file.originalname}`);
        try {
            const keywords = await this.parseKeywordsFromCsv(file);
            this.logger.log(`Extracted ${keywords.length} keywords from CSV`);
            if (keywords.length === 0) {
                throw new common_1.InternalServerErrorException('No valid keywords found in CSV file');
            }
            const searchJob = new search_account_job_entity_1.SearchAccountJob();
            searchJob.keywords = keywords;
            searchJob.totalKeywords = keywords.length;
            searchJob.status = search_account_job_entity_1.SearchAccountJobStatus.PENDING;
            searchJob.processedKeywords = 0;
            searchJob.totalFoundAccounts = 0;
            searchJob.filteredAccounts = 0;
            const jobParams = {
                resultsPerKeyword: dto.resultsPerKeyword || 100,
                minFollowerCount: dto.minFollowers || 10000,
                maxFollowerCount: dto.maxFollowers,
                includePrivateAccounts: dto.includePrivateAccounts || false,
                minMediaCount: dto.minPostsInLastMonth || 1,
                requireVerified: dto.requireVerified || false,
                requireBusiness: dto.requireBusiness || false,
            };
            try {
                searchJob.jobData = jobParams;
            }
            catch {
                this.logger.warn('jobData column does not exist yet, using default filter values');
            }
            this.logger.log(`Saving job to database...`);
            const savedJob = (await Promise.race([
                this.searchJobRepository.save(searchJob),
                new Promise((_, reject) => setTimeout(() => reject(new Error('Database save timeout')), 10000)),
            ]));
            const jobData = {
                jobId: savedJob.id,
                keywords: keywords,
                resultsPerKeyword: dto.resultsPerKeyword || 100,
                minFollowerCount: dto.minFollowers || 10000,
                maxFollowerCount: dto.maxFollowers,
                includePrivateAccounts: dto.includePrivateAccounts || false,
                minMediaCount: dto.minPostsInLastMonth || 1,
                requireVerified: dto.requireVerified || false,
                requireBusiness: dto.requireBusiness || false,
            };
            this.logger.log(`Sending job to SQS queue...`);
            await Promise.race([
                this.searchSqsService.sendMessage(jobData),
                new Promise((_, reject) => setTimeout(() => reject(new Error('SQS send timeout')), 10000)),
            ]);
            const estimatedTimeMinutes = Math.ceil((keywords.length * 2) / 60);
            return {
                searchAccountsId: savedJob.id,
                status: search_account_job_entity_1.SearchAccountJobStatus.PENDING,
                totalKeywords: keywords.length,
                estimatedTimeMinutes,
                message: 'CSV search job started successfully',
            };
        }
        catch (error) {
            this.logger.error(`Error starting CSV search: ${error.message}`, error.stack);
            if (error.message === 'Database save timeout') {
                throw new common_1.InternalServerErrorException('Database connection timeout. Please try again.');
            }
            else if (error.message === 'SQS send timeout') {
                throw new common_1.InternalServerErrorException('SQS queue connection timeout. Please try again.');
            }
            throw new common_1.InternalServerErrorException(`Failed to start CSV search job: ${error.message}`);
        }
    }
    async parseKeywordsFromCsv(file) {
        return new Promise((resolve, reject) => {
            const keywords = [];
            const stream = stream_1.Readable.from(file.buffer);
            stream
                .pipe(csv())
                .on('data', (row) => {
                const firstColumnValue = Object.values(row)[0];
                if (firstColumnValue && typeof firstColumnValue === 'string') {
                    const keyword = firstColumnValue.trim();
                    if (keyword &&
                        keyword.toLowerCase() !== 'keyword' &&
                        keyword.toLowerCase() !== 'keywords' &&
                        keyword.toLowerCase() !== 'search_term' &&
                        keyword.toLowerCase() !== 'term') {
                        keywords.push(keyword);
                    }
                }
            })
                .on('end', () => {
                this.logger.log(`Parsed ${keywords.length} keywords from CSV`);
                resolve(keywords);
            })
                .on('error', (error) => {
                this.logger.error(`Error parsing CSV: ${error.message}`);
                reject(new common_1.InternalServerErrorException('Failed to parse CSV file'));
            });
        });
    }
    async healthCheck() {
        const results = {
            timestamp: new Date().toISOString(),
            database: { connected: false, responseTime: 0 },
            redis: { connected: false, responseTime: 0 },
            overall: 'unhealthy',
        };
        try {
            const start = Date.now();
            await this.searchJobRepository.query('SELECT 1');
            results.database.connected = true;
            results.database.responseTime = Date.now() - start;
            this.logger.log(`Database connection OK (${results.database.responseTime}ms)`);
        }
        catch (error) {
            this.logger.error(`Database connection failed: ${error.message}`);
            results.database = {
                connected: false,
                responseTime: 0,
                error: error.message,
            };
        }
        try {
            const start = Date.now();
            await this.searchSqsService.sendMessage({
                type: 'healthCheck',
                timestamp: new Date().toISOString(),
            });
            results.redis.connected = true;
            results.redis.responseTime = Date.now() - start;
            this.logger.log(`SQS connection OK (${results.redis.responseTime}ms)`);
        }
        catch (error) {
            this.logger.error(`SQS connection failed: ${error.message}`);
            results.redis = {
                connected: false,
                responseTime: 0,
                error: error.message,
            };
        }
        results.overall =
            results.database.connected && results.redis.connected
                ? 'healthy'
                : 'unhealthy';
        return results;
    }
    async getJobStatus(searchAccountsId) {
        this.logger.log(`Getting status for job ${searchAccountsId}`);
        try {
            const job = await this.searchJobRepository.findOne({
                where: { id: searchAccountsId },
            });
            if (!job) {
                throw new common_1.NotFoundException(`Search job ${searchAccountsId} not found`);
            }
            const progressPercentage = job.totalKeywords > 0
                ? Math.round((job.processedKeywords / job.totalKeywords) * 100)
                : 0;
            let estimatedTimeRemainingMinutes;
            if (job.status === search_account_job_entity_1.SearchAccountJobStatus.PROCESSING && job.startedAt) {
                const elapsedMinutes = (Date.now() - job.startedAt.getTime()) / (1000 * 60);
                const remainingKeywords = job.totalKeywords - job.processedKeywords;
                const avgTimePerKeyword = elapsedMinutes / Math.max(job.processedKeywords, 1);
                estimatedTimeRemainingMinutes = Math.ceil(remainingKeywords * avgTimePerKeyword);
            }
            return {
                searchAccountsId: job.id,
                status: job.status,
                createdAt: job.createdAt,
                startedAt: job.startedAt,
                completedAt: job.completedAt,
                totalKeywords: job.totalKeywords,
                processedKeywords: job.processedKeywords,
                totalFoundAccounts: job.totalFoundAccounts,
                filteredAccounts: job.filteredAccounts,
                csvFileUrl: job.csvFileUrl,
                progressPercentage,
                errorMessage: job.errorMessage,
                estimatedTimeRemainingMinutes,
            };
        }
        catch (error) {
            if (error instanceof common_1.NotFoundException) {
                throw error;
            }
            this.logger.error(`Error getting job status: ${error.message}`);
            throw new common_1.InternalServerErrorException('Failed to get job status');
        }
    }
    async generateCsvForJob(searchAccountsId) {
        this.logger.log(`Generating CSV for job ${searchAccountsId}`);
        try {
            const job = await this.searchJobRepository.findOne({
                where: { id: searchAccountsId },
            });
            if (!job) {
                throw new common_1.NotFoundException(`Search job ${searchAccountsId} not found`);
            }
            if (job.status !== search_account_job_entity_1.SearchAccountJobStatus.COMPLETED) {
                throw new common_1.InternalServerErrorException('Job is not completed yet');
            }
            const results = await this.searchResultRepository.find({
                where: {
                    jobId: searchAccountsId,
                    passedFilter: true,
                },
                order: { keyword: 'ASC', username: 'ASC' },
            });
            if (results.length === 0) {
                throw new common_1.NotFoundException('No filtered results available for this job');
            }
            const csvHeader = [
                'Keyword',
                'Username',
                'User ID',
                'Full Name',
                'Follower Count',
                'Following Count',
                'Media Count',
                'Is Verified',
                'Is Business',
                'Category',
                'Biography',
                'External URL',
            ].join(',') + '\n';
            const csvRows = results.map((result) => [
                `"${result.keyword}"`,
                `"${result.username}"`,
                `"${result.userPk}"`,
                `"${result.fullName || ''}"`,
                result.followerCount,
                result.followingCount,
                result.mediaCount,
                result.isVerified ? 'Yes' : 'No',
                result.isBusiness ? 'Yes' : 'No',
                `"${result.category || ''}"`,
                `"${(result.biography || '').replace(/"/g, '""')}"`,
                `"${result.externalUrl || ''}"`,
            ].join(','));
            return csvHeader + csvRows.join('\n');
        }
        catch (error) {
            if (error instanceof common_1.NotFoundException ||
                error instanceof common_1.InternalServerErrorException) {
                throw error;
            }
            this.logger.error(`Error generating CSV: ${error.message}`);
            throw new common_1.InternalServerErrorException('Failed to generate CSV');
        }
    }
};
exports.SearchAccountsService = SearchAccountsService;
exports.SearchAccountsService = SearchAccountsService = SearchAccountsService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(1, (0, typeorm_1.InjectRepository)(search_account_job_entity_1.SearchAccountJob)),
    __param(2, (0, typeorm_1.InjectRepository)(search_account_result_entity_1.SearchAccountResult)),
    __param(3, (0, common_2.Inject)(aws_module_1.SQS_SEARCH_ACCOUNTS_SERVICE)),
    __metadata("design:paramtypes", [hiker_api_client_service_1.HikerApiClientService,
        typeorm_2.Repository,
        typeorm_2.Repository,
        aws_sqs_service_1.AwsSqsService])
], SearchAccountsService);
//# sourceMappingURL=search-accounts.service.js.map