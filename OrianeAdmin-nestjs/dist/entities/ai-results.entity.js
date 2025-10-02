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
exports.AiResult = void 0;
const typeorm_1 = require("typeorm");
const ai_jobs_entity_1 = require("./ai-jobs.entity");
const ai_jobs_run_entity_1 = require("./ai-jobs-run.entity");
const content_entity_1 = require("./content.entity");
let AiResult = class AiResult {
};
exports.AiResult = AiResult;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], AiResult.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_ai_results_job_id'),
    (0, typeorm_1.Column)({ type: 'uuid', name: 'job_id', nullable: true }),
    __metadata("design:type", String)
], AiResult.prototype, "jobId", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => ai_jobs_entity_1.AiJob, (job) => job.id, {
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
        nullable: true,
    }),
    (0, typeorm_1.JoinColumn)({ name: 'job_id' }),
    __metadata("design:type", ai_jobs_entity_1.AiJob)
], AiResult.prototype, "aiJob", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_ai_results_created_at'),
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], AiResult.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_ai_results_monitored_video'),
    (0, typeorm_1.Column)({ type: 'varchar', name: 'monitored_video', nullable: false }),
    __metadata("design:type", String)
], AiResult.prototype, "monitoredVideo", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => content_entity_1.InstaContent, {
        onDelete: 'NO ACTION',
        onUpdate: 'NO ACTION',
    }),
    (0, typeorm_1.JoinColumn)({ name: 'monitored_video', referencedColumnName: 'code' }),
    __metadata("design:type", content_entity_1.InstaContent)
], AiResult.prototype, "monitoredInstaContent", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_ai_results_watched_video'),
    (0, typeorm_1.Column)({ type: 'varchar', name: 'watched_video', nullable: false }),
    __metadata("design:type", String)
], AiResult.prototype, "watchedVideo", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => content_entity_1.InstaContent, {
        onDelete: 'NO ACTION',
        onUpdate: 'NO ACTION',
    }),
    (0, typeorm_1.JoinColumn)({ name: 'watched_video', referencedColumnName: 'code' }),
    __metadata("design:type", content_entity_1.InstaContent)
], AiResult.prototype, "watchedInstaContent", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'real', name: 'avg_similarity', nullable: true }),
    __metadata("design:type", Number)
], AiResult.prototype, "avgSimilarity", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'real', name: 'processed_in_secs', nullable: true }),
    __metadata("design:type", Number)
], AiResult.prototype, "processedInSecs", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'jsonb', name: 'frame_results', nullable: true }),
    __metadata("design:type", Array)
], AiResult.prototype, "frameResults", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_ai_results_max_similarity'),
    (0, typeorm_1.Column)({ type: 'real', name: 'max_similarity', nullable: true }),
    __metadata("design:type", Number)
], AiResult.prototype, "maxSimilarity", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'varchar',
        name: 'model',
        nullable: false,
        default: 'FCM',
    }),
    __metadata("design:type", String)
], AiResult.prototype, "model", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'real', nullable: false }),
    __metadata("design:type", Number)
], AiResult.prototype, "similarity", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'real', name: 'std_similarity', nullable: true }),
    __metadata("design:type", Number)
], AiResult.prototype, "stdSimilarity", void 0);
__decorate([
    (0, typeorm_1.Index)(),
    (0, typeorm_1.Column)({ type: 'uuid', name: 'job_run_id', nullable: true }),
    __metadata("design:type", String)
], AiResult.prototype, "jobRunId", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => ai_jobs_run_entity_1.AiJobsRun, (run) => run.id, {
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
        nullable: true,
    }),
    (0, typeorm_1.JoinColumn)({ name: 'job_run_id' }),
    __metadata("design:type", ai_jobs_run_entity_1.AiJobsRun)
], AiResult.prototype, "aiJobsRun", void 0);
exports.AiResult = AiResult = __decorate([
    (0, typeorm_1.Entity)('ai_results')
], AiResult);
//# sourceMappingURL=ai-results.entity.js.map