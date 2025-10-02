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
var SearchAccountsController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.SearchAccountsController = void 0;
const common_1 = require("@nestjs/common");
const platform_express_1 = require("@nestjs/platform-express");
const swagger_1 = require("@nestjs/swagger");
const jwt_auth_guard_1 = require("../../guards/jwt-auth.guard");
const search_accounts_service_1 = require("./search-accounts.service");
const search_accounts_dto_1 = require("./dto/search-accounts.dto");
const bulk_search_accounts_dto_1 = require("./dto/bulk-search-accounts.dto");
let SearchAccountsController = SearchAccountsController_1 = class SearchAccountsController {
    constructor(searchAccountsService) {
        this.searchAccountsService = searchAccountsService;
        this.logger = new common_1.Logger(SearchAccountsController_1.name);
    }
    async searchAccountsByKeyword(dto) {
        this.logger.log(`Received keyword search request for: ${dto.keyword}`);
        const results = await this.searchAccountsService.searchAccountsByKeyword(dto);
        return {
            success: true,
            data: {
                keyword: dto.keyword,
                count: results.length,
                accounts: results,
            },
            message: `Found ${results.length} accounts for keyword "${dto.keyword}"`,
        };
    }
    async startBulkSearch(dto) {
        this.logger.log(`Received bulk search request for ${dto.keywords.length} keywords`);
        const result = await this.searchAccountsService.startBulkSearch(dto);
        return result;
    }
    async startCsvSearch(file, dto) {
        this.logger.log(`Received CSV search request with file: ${file?.originalname || 'No file'}`);
        if (!file) {
            throw new common_1.BadRequestException('No CSV file uploaded');
        }
        if (!file.mimetype.includes('csv') && !file.originalname.endsWith('.csv')) {
            throw new common_1.BadRequestException('File must be a CSV file');
        }
        const result = await this.searchAccountsService.startCsvSearch(file, dto);
        return result;
    }
    async getJobStatus(searchAccountsId) {
        this.logger.log(`Received status request for job: ${searchAccountsId}`);
        const status = await this.searchAccountsService.getJobStatus(searchAccountsId);
        return status;
    }
    async downloadResults(searchAccountsId, res) {
        this.logger.log(`Received download request for job: ${searchAccountsId}`);
        try {
            const csvContent = await this.searchAccountsService.generateCsvForJob(searchAccountsId);
            const fileName = `search-accounts-${searchAccountsId}-${Date.now()}.csv`;
            res.setHeader('Content-Type', 'text/csv');
            res.setHeader('Content-Disposition', `attachment; filename="${fileName}"`);
            res.setHeader('Content-Length', Buffer.byteLength(csvContent, 'utf8'));
            res.send(csvContent);
        }
        catch (error) {
            res.status(error.status || common_1.HttpStatus.INTERNAL_SERVER_ERROR).json({
                error: error.message,
            });
        }
    }
};
exports.SearchAccountsController = SearchAccountsController;
__decorate([
    (0, common_1.Post)('search-keyword'),
    (0, swagger_1.ApiOperation)({
        summary: 'Search accounts by single keyword',
        description: 'Search for Instagram accounts using a single keyword via Hiker API',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Successfully retrieved accounts for the keyword',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid keyword or parameters provided',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.INTERNAL_SERVER_ERROR,
        description: 'Failed to search accounts',
    }),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [search_accounts_dto_1.SearchAccountsByKeywordDto]),
    __metadata("design:returntype", Promise)
], SearchAccountsController.prototype, "searchAccountsByKeyword", null);
__decorate([
    (0, common_1.Post)('bulk-search'),
    (0, swagger_1.ApiOperation)({
        summary: 'Start bulk search across multiple keywords',
        description: 'Start an async bulk search job for multiple keywords with filtering. Returns a job ID to track progress.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Bulk search job started successfully',
        type: bulk_search_accounts_dto_1.BulkSearchResponseDto,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid keywords or parameters provided',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.INTERNAL_SERVER_ERROR,
        description: 'Failed to start bulk search job',
    }),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [bulk_search_accounts_dto_1.BulkSearchAccountsDto]),
    __metadata("design:returntype", Promise)
], SearchAccountsController.prototype, "startBulkSearch", null);
__decorate([
    (0, common_1.Post)('csv-search'),
    (0, swagger_1.ApiOperation)({
        summary: 'Start bulk search from CSV file',
        description: 'Upload a CSV file with keywords in the first column to start an async bulk search job. Can handle millions of keywords unlike the regular bulk search endpoint.',
    }),
    (0, swagger_1.ApiConsumes)('multipart/form-data'),
    (0, swagger_1.ApiBody)({
        schema: {
            type: 'object',
            properties: {
                file: {
                    type: 'string',
                    format: 'binary',
                    description: 'CSV file with keywords in the first column',
                },
                resultsPerKeyword: {
                    type: 'number',
                    description: 'Number of results per keyword (1-1000)',
                    default: 100,
                },
                minFollowers: {
                    type: 'number',
                    description: 'Minimum follower count filter',
                    default: 10000,
                },
                maxFollowers: {
                    type: 'number',
                    description: 'Maximum follower count filter',
                },
                minPostsInLastMonth: {
                    type: 'number',
                    description: 'Minimum posts in last 30 days',
                    default: 1,
                },
                requireVerified: {
                    type: 'boolean',
                    description: 'Only include verified accounts',
                    default: false,
                },
                requireBusiness: {
                    type: 'boolean',
                    description: 'Only include business accounts',
                    default: false,
                },
                includePrivateAccounts: {
                    type: 'boolean',
                    description: 'Include private accounts',
                    default: false,
                },
            },
            required: ['file'],
        },
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'CSV search job started successfully',
        type: bulk_search_accounts_dto_1.BulkSearchResponseDto,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid CSV file or parameters provided',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.INTERNAL_SERVER_ERROR,
        description: 'Failed to start CSV search job',
    }),
    (0, common_1.UseInterceptors)((0, platform_express_1.FileInterceptor)('file')),
    __param(0, (0, common_1.UploadedFile)()),
    __param(1, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object, bulk_search_accounts_dto_1.CsvSearchAccountsDto]),
    __metadata("design:returntype", Promise)
], SearchAccountsController.prototype, "startCsvSearch", null);
__decorate([
    (0, common_1.Get)('job/:searchAccountsId/status'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get bulk search job status',
        description: 'Check the status of a bulk search job, including progress and results when complete.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Job status retrieved successfully',
        type: bulk_search_accounts_dto_1.SearchJobStatusDto,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'Search job not found',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.INTERNAL_SERVER_ERROR,
        description: 'Failed to get job status',
    }),
    __param(0, (0, common_1.Param)('searchAccountsId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], SearchAccountsController.prototype, "getJobStatus", null);
__decorate([
    (0, common_1.Get)('job/:searchAccountsId/download'),
    (0, swagger_1.ApiOperation)({
        summary: 'Download CSV results',
        description: 'Download the filtered results as a CSV file. Only available when job is completed.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'CSV file downloaded successfully',
        content: {
            'text/csv': {
                schema: {
                    type: 'string',
                    format: 'binary',
                },
            },
        },
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'Search job not found or no results available',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Job is not completed yet',
    }),
    __param(0, (0, common_1.Param)('searchAccountsId')),
    __param(1, (0, common_1.Res)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", Promise)
], SearchAccountsController.prototype, "downloadResults", null);
exports.SearchAccountsController = SearchAccountsController = SearchAccountsController_1 = __decorate([
    (0, swagger_1.ApiTags)('Search For Accounts'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Controller)('search-accounts/instagram/'),
    __metadata("design:paramtypes", [search_accounts_service_1.SearchAccountsService])
], SearchAccountsController);
//# sourceMappingURL=search-accounts.controller.js.map