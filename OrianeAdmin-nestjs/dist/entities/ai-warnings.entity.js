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
exports.AiWarning = void 0;
const typeorm_1 = require("typeorm");
const ai_jobs_entity_1 = require("./ai-jobs.entity");
const ai_jobs_run_entity_1 = require("./ai-jobs-run.entity");
let AiWarning = class AiWarning {
};
exports.AiWarning = AiWarning;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], AiWarning.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], AiWarning.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.Index)(),
    (0, typeorm_1.Column)({ type: 'uuid', name: 'job_id', nullable: false }),
    __metadata("design:type", String)
], AiWarning.prototype, "jobId", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => ai_jobs_entity_1.AiJob, {
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
        nullable: false,
    }),
    (0, typeorm_1.JoinColumn)({ name: 'job_id' }),
    __metadata("design:type", ai_jobs_entity_1.AiJob)
], AiWarning.prototype, "aiJob", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'watched_video', nullable: false }),
    __metadata("design:type", String)
], AiWarning.prototype, "watchedVideo", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'text', name: 'warning_message', nullable: false }),
    __metadata("design:type", String)
], AiWarning.prototype, "warningMessage", void 0);
__decorate([
    (0, typeorm_1.Index)(),
    (0, typeorm_1.Column)({ type: 'uuid', name: 'job_run_id', nullable: true }),
    __metadata("design:type", String)
], AiWarning.prototype, "jobRunId", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => ai_jobs_run_entity_1.AiJobsRun, {
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
        nullable: true,
    }),
    (0, typeorm_1.JoinColumn)({ name: 'job_run_id' }),
    __metadata("design:type", ai_jobs_run_entity_1.AiJobsRun)
], AiWarning.prototype, "aiJobsRun", void 0);
exports.AiWarning = AiWarning = __decorate([
    (0, typeorm_1.Entity)('ai_warnings')
], AiWarning);
//# sourceMappingURL=ai-warnings.entity.js.map