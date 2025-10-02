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
exports.AiJob = void 0;
const typeorm_1 = require("typeorm");
const ai_jobs_run_entity_1 = require("./ai-jobs-run.entity");
let AiJob = class AiJob {
};
exports.AiJob = AiJob;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], AiJob.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], AiJob.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', name: 'model', nullable: false }),
    __metadata("design:type", String)
], AiJob.prototype, "model", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'boolean', name: 'use_gpu', default: false, nullable: false }),
    __metadata("design:type", Boolean)
], AiJob.prototype, "useGpu", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_ai_jobs_monitored_video'),
    (0, typeorm_1.Column)({ type: 'varchar', name: 'monitored_video', nullable: false }),
    __metadata("design:type", String)
], AiJob.prototype, "monitoredVideo", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'published_date',
        type: 'timestamp with time zone',
        nullable: false,
    }),
    __metadata("design:type", Date)
], AiJob.prototype, "publishedDate", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'threshold',
        type: 'real',
        default: 0.5,
        nullable: false,
    }),
    __metadata("design:type", Number)
], AiJob.prototype, "threshold", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => ai_jobs_run_entity_1.AiJobsRun, (run) => run.aiJob, {}),
    __metadata("design:type", Array)
], AiJob.prototype, "runs", void 0);
exports.AiJob = AiJob = __decorate([
    (0, typeorm_1.Entity)('ai_jobs')
], AiJob);
//# sourceMappingURL=ai-jobs.entity.js.map