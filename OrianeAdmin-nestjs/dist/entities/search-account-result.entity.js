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
exports.SearchAccountResult = void 0;
const typeorm_1 = require("typeorm");
const search_account_job_entity_1 = require("./search-account-job.entity");
let SearchAccountResult = class SearchAccountResult {
};
exports.SearchAccountResult = SearchAccountResult;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], SearchAccountResult.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_search_account_results_job_id'),
    (0, typeorm_1.Column)({ type: 'uuid', name: 'job_id', nullable: false }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "jobId", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', nullable: false }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "keyword", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_search_account_results_username'),
    (0, typeorm_1.Column)({ type: 'varchar', nullable: false }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "username", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'user_pk', nullable: false }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "userPk", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'full_name', nullable: true }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "fullName", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'boolean', name: 'is_private', nullable: false }),
    __metadata("design:type", Boolean)
], SearchAccountResult.prototype, "isPrivate", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'profile_pic_url', nullable: true }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "profilePicUrl", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'boolean', name: 'is_verified', nullable: false }),
    __metadata("design:type", Boolean)
], SearchAccountResult.prototype, "isVerified", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', name: 'media_count', nullable: false }),
    __metadata("design:type", Number)
], SearchAccountResult.prototype, "mediaCount", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', name: 'follower_count', nullable: false }),
    __metadata("design:type", Number)
], SearchAccountResult.prototype, "followerCount", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', name: 'following_count', nullable: false }),
    __metadata("design:type", Number)
], SearchAccountResult.prototype, "followingCount", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'text', nullable: true }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "biography", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'external_url', nullable: true }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "externalUrl", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'account_type', nullable: true }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "accountType", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'boolean', name: 'is_business', nullable: false }),
    __metadata("design:type", Boolean)
], SearchAccountResult.prototype, "isBusiness", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', nullable: true }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "category", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'boolean', name: 'passed_filter', default: false, nullable: false }),
    __metadata("design:type", Boolean)
], SearchAccountResult.prototype, "passedFilter", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'filter_reason', nullable: true }),
    __metadata("design:type", String)
], SearchAccountResult.prototype, "filterReason", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => search_account_job_entity_1.SearchAccountJob, (job) => job.results, {
        onDelete: 'CASCADE',
    }),
    (0, typeorm_1.JoinColumn)({ name: 'job_id' }),
    __metadata("design:type", search_account_job_entity_1.SearchAccountJob)
], SearchAccountResult.prototype, "job", void 0);
exports.SearchAccountResult = SearchAccountResult = __decorate([
    (0, typeorm_1.Entity)('search_account_results')
], SearchAccountResult);
//# sourceMappingURL=search-account-result.entity.js.map