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
exports.AiJobsRun = void 0;
const typeorm_1 = require("typeorm");
const ai_jobs_entity_1 = require("./ai-jobs.entity");
let AiJobsRun = class AiJobsRun {
};
exports.AiJobsRun = AiJobsRun;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], AiJobsRun.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], AiJobsRun.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.Index)(),
    (0, typeorm_1.Column)({ type: 'uuid', name: 'job_id', nullable: false }),
    __metadata("design:type", String)
], AiJobsRun.prototype, "jobId", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => ai_jobs_entity_1.AiJob, (job) => job.runs, {
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
        nullable: false,
    }),
    (0, typeorm_1.JoinColumn)({ name: 'job_id' }),
    __metadata("design:type", ai_jobs_entity_1.AiJob)
], AiJobsRun.prototype, "aiJob", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'bigint', name: 'comparisons_to_process', nullable: false }),
    __metadata("design:type", Number)
], AiJobsRun.prototype, "comparisonsToProcess", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'bigint',
        name: 'comparisons_processed',
        default: 0,
        nullable: false,
    }),
    __metadata("design:type", Number)
], AiJobsRun.prototype, "comparisonsProcessed", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'bigint',
        name: 'comparisons_failed',
        default: 0,
        nullable: false,
    }),
    __metadata("design:type", Number)
], AiJobsRun.prototype, "comparisonsFailed", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'last_video_code', nullable: true }),
    __metadata("design:type", String)
], AiJobsRun.prototype, "lastVideoCode", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'timestamp with time zone',
        name: 'last_published_date',
        nullable: true,
    }),
    __metadata("design:type", Date)
], AiJobsRun.prototype, "lastPublishedDate", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'timestamp with time zone',
        name: 'started_at',
        nullable: true,
    }),
    __metadata("design:type", Date)
], AiJobsRun.prototype, "startedAt", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'timestamp with time zone',
        name: 'finished_at',
        nullable: true,
    }),
    __metadata("design:type", Date)
], AiJobsRun.prototype, "finishedAt", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'varchar',
        name: 'state',
        nullable: false,
    }),
    __metadata("design:type", String)
], AiJobsRun.prototype, "state", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'bigint',
        name: 'warnings_count',
        default: 0,
        nullable: false,
    }),
    __metadata("design:type", Number)
], AiJobsRun.prototype, "warningsCount", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'real', name: 'estimated_cost', default: 0, nullable: false }),
    __metadata("design:type", Number)
], AiJobsRun.prototype, "estimatedCost", void 0);
exports.AiJobsRun = AiJobsRun = __decorate([
    (0, typeorm_1.Entity)('ai_jobs_runs')
], AiJobsRun);
//# sourceMappingURL=ai-jobs-run.entity.js.map