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
Object.defineProperty(exports, "__esModule", { value: true });
exports.CsvSearchAccountsDto = exports.SearchJobStatusDto = exports.BulkSearchResponseDto = exports.BulkSearchAccountsDto = void 0;
const swagger_1 = require("@nestjs/swagger");
const class_validator_1 = require("class-validator");
const class_transformer_1 = require("class-transformer");
const search_account_job_entity_1 = require("../../../entities/search-account-job.entity");
class BulkSearchAccountsDto {
    constructor() {
        this.resultsPerKeyword = 100;
        this.minFollowers = 10000;
        this.minPostsInLastMonth = 1;
        this.requireVerified = false;
        this.requireBusiness = false;
        this.includePrivateAccounts = false;
    }
}
exports.BulkSearchAccountsDto = BulkSearchAccountsDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Array of keywords to search for accounts',
        example: ['fashion', 'food', 'tennis', 'meme', 'news'],
        minItems: 1,
        maxItems: 10000,
    }),
    (0, class_validator_1.IsArray)(),
    (0, class_validator_1.ArrayMinSize)(1),
    (0, class_validator_1.ArrayMaxSize)(10000),
    (0, class_validator_1.IsString)({ each: true }),
    __metadata("design:type", Array)
], BulkSearchAccountsDto.prototype, "keywords", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Number of results to return per keyword (max 1000)',
        example: 100,
        default: 100,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(1),
    (0, class_validator_1.Max)(1000),
    __metadata("design:type", Number)
], BulkSearchAccountsDto.prototype, "resultsPerKeyword", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Minimum follower count filter',
        example: 10000,
        default: 10000,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], BulkSearchAccountsDto.prototype, "minFollowers", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Maximum follower count filter (optional upper limit)',
        example: 100000000,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], BulkSearchAccountsDto.prototype, "maxFollowers", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Minimum posts in the last 30 days (checks recent activity)',
        example: 1,
        default: 1,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], BulkSearchAccountsDto.prototype, "minPostsInLastMonth", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Only include verified accounts',
        example: false,
        default: false,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Boolean),
    __metadata("design:type", Boolean)
], BulkSearchAccountsDto.prototype, "requireVerified", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Only include business accounts',
        example: false,
        default: false,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Boolean),
    __metadata("design:type", Boolean)
], BulkSearchAccountsDto.prototype, "requireBusiness", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Include private accounts in results',
        example: false,
        default: false,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Boolean),
    __metadata("design:type", Boolean)
], BulkSearchAccountsDto.prototype, "includePrivateAccounts", void 0);
class BulkSearchResponseDto {
}
exports.BulkSearchResponseDto = BulkSearchResponseDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Unique identifier for the bulk search job',
        example: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    }),
    __metadata("design:type", String)
], BulkSearchResponseDto.prototype, "searchAccountsId", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Current status of the job',
        enum: search_account_job_entity_1.SearchAccountJobStatus,
    }),
    __metadata("design:type", String)
], BulkSearchResponseDto.prototype, "status", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Total number of keywords to process',
        example: 5,
    }),
    __metadata("design:type", Number)
], BulkSearchResponseDto.prototype, "totalKeywords", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Estimated processing time in minutes',
        example: 15,
    }),
    __metadata("design:type", Number)
], BulkSearchResponseDto.prototype, "estimatedTimeMinutes", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Success message',
        example: 'Bulk search job started successfully',
    }),
    __metadata("design:type", String)
], BulkSearchResponseDto.prototype, "message", void 0);
class SearchJobStatusDto {
}
exports.SearchJobStatusDto = SearchJobStatusDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Unique identifier for the bulk search job',
        example: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    }),
    __metadata("design:type", String)
], SearchJobStatusDto.prototype, "searchAccountsId", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Current status of the job',
        enum: search_account_job_entity_1.SearchAccountJobStatus,
    }),
    __metadata("design:type", String)
], SearchJobStatusDto.prototype, "status", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Job creation timestamp',
    }),
    __metadata("design:type", Date)
], SearchJobStatusDto.prototype, "createdAt", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Job start timestamp',
        required: false,
    }),
    __metadata("design:type", Date)
], SearchJobStatusDto.prototype, "startedAt", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Job completion timestamp',
        required: false,
    }),
    __metadata("design:type", Date)
], SearchJobStatusDto.prototype, "completedAt", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Total number of keywords to process',
        example: 5,
    }),
    __metadata("design:type", Number)
], SearchJobStatusDto.prototype, "totalKeywords", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Number of keywords processed',
        example: 3,
    }),
    __metadata("design:type", Number)
], SearchJobStatusDto.prototype, "processedKeywords", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Total accounts found across all keywords',
        example: 1500,
    }),
    __metadata("design:type", Number)
], SearchJobStatusDto.prototype, "totalFoundAccounts", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Number of accounts that passed filters',
        example: 243,
    }),
    __metadata("design:type", Number)
], SearchJobStatusDto.prototype, "filteredAccounts", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'URL to download CSV file when job is completed',
        required: false,
    }),
    __metadata("design:type", String)
], SearchJobStatusDto.prototype, "csvFileUrl", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Progress percentage (0-100)',
        example: 60,
    }),
    __metadata("design:type", Number)
], SearchJobStatusDto.prototype, "progressPercentage", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Error message if job failed',
        required: false,
    }),
    __metadata("design:type", String)
], SearchJobStatusDto.prototype, "errorMessage", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Estimated time remaining in minutes',
        required: false,
    }),
    __metadata("design:type", Number)
], SearchJobStatusDto.prototype, "estimatedTimeRemainingMinutes", void 0);
class CsvSearchAccountsDto {
    constructor() {
        this.resultsPerKeyword = 100;
        this.minFollowers = 10000;
        this.minPostsInLastMonth = 1;
        this.requireVerified = false;
        this.requireBusiness = false;
        this.includePrivateAccounts = false;
    }
}
exports.CsvSearchAccountsDto = CsvSearchAccountsDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Number of results to return per keyword (max 1000)',
        example: 100,
        default: 100,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(1),
    (0, class_validator_1.Max)(1000),
    __metadata("design:type", Number)
], CsvSearchAccountsDto.prototype, "resultsPerKeyword", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Minimum follower count filter',
        example: 10000,
        default: 10000,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], CsvSearchAccountsDto.prototype, "minFollowers", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Maximum follower count filter (optional upper limit)',
        example: 100000000,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], CsvSearchAccountsDto.prototype, "maxFollowers", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Minimum posts in the last 30 days (checks recent activity)',
        example: 1,
        default: 1,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], CsvSearchAccountsDto.prototype, "minPostsInLastMonth", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Only include verified accounts',
        example: false,
        default: false,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Boolean),
    (0, class_validator_1.IsBoolean)(),
    __metadata("design:type", Boolean)
], CsvSearchAccountsDto.prototype, "requireVerified", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Only include business accounts',
        example: false,
        default: false,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Boolean),
    (0, class_validator_1.IsBoolean)(),
    __metadata("design:type", Boolean)
], CsvSearchAccountsDto.prototype, "requireBusiness", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Include private accounts in results',
        example: false,
        default: false,
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Boolean),
    (0, class_validator_1.IsBoolean)(),
    __metadata("design:type", Boolean)
], CsvSearchAccountsDto.prototype, "includePrivateAccounts", void 0);
//# sourceMappingURL=bulk-search-accounts.dto.js.map