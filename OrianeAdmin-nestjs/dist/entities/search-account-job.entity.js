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
exports.SearchAccountJob = exports.SearchAccountJobStatus = void 0;
const typeorm_1 = require("typeorm");
const search_account_result_entity_1 = require("./search-account-result.entity");
var SearchAccountJobStatus;
(function (SearchAccountJobStatus) {
    SearchAccountJobStatus["PENDING"] = "pending";
    SearchAccountJobStatus["PROCESSING"] = "processing";
    SearchAccountJobStatus["COMPLETED"] = "completed";
    SearchAccountJobStatus["FAILED"] = "failed";
})(SearchAccountJobStatus || (exports.SearchAccountJobStatus = SearchAccountJobStatus = {}));
let SearchAccountJob = class SearchAccountJob {
};
exports.SearchAccountJob = SearchAccountJob;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], SearchAccountJob.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], SearchAccountJob.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.UpdateDateColumn)({
        name: 'updated_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], SearchAccountJob.prototype, "updatedAt", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_search_account_jobs_status'),
    (0, typeorm_1.Column)({
        type: 'enum',
        enum: SearchAccountJobStatus,
        default: SearchAccountJobStatus.PENDING,
        nullable: false,
    }),
    __metadata("design:type", String)
], SearchAccountJob.prototype, "status", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'text', array: true, nullable: false }),
    __metadata("design:type", Array)
], SearchAccountJob.prototype, "keywords", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', name: 'total_keywords', nullable: false }),
    __metadata("design:type", Number)
], SearchAccountJob.prototype, "totalKeywords", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', name: 'processed_keywords', default: 0, nullable: false }),
    __metadata("design:type", Number)
], SearchAccountJob.prototype, "processedKeywords", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', name: 'total_found_accounts', default: 0, nullable: false }),
    __metadata("design:type", Number)
], SearchAccountJob.prototype, "totalFoundAccounts", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', name: 'filtered_accounts', default: 0, nullable: false }),
    __metadata("design:type", Number)
], SearchAccountJob.prototype, "filteredAccounts", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'csv_file_url', nullable: true }),
    __metadata("design:type", String)
], SearchAccountJob.prototype, "csvFileUrl", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'error_message', nullable: true }),
    __metadata("design:type", String)
], SearchAccountJob.prototype, "errorMessage", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'jsonb', name: 'job_data', nullable: true, select: false }),
    __metadata("design:type", Object)
], SearchAccountJob.prototype, "jobData", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'started_at',
        type: 'timestamp with time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], SearchAccountJob.prototype, "startedAt", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'completed_at',
        type: 'timestamp with time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], SearchAccountJob.prototype, "completedAt", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => search_account_result_entity_1.SearchAccountResult, (result) => result.job, {
        cascade: true,
    }),
    __metadata("design:type", Array)
], SearchAccountJob.prototype, "results", void 0);
exports.SearchAccountJob = SearchAccountJob = __decorate([
    (0, typeorm_1.Entity)('search_account_jobs')
], SearchAccountJob);
//# sourceMappingURL=search-account-job.entity.js.map