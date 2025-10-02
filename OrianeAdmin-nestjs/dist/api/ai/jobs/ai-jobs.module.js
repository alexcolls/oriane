"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AiJobsModule = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const bull_1 = require("@nestjs/bull");
const aws_module_1 = require("../../../aws/aws.module");
const ai_jobs_controller_1 = require("./ai-jobs.controller");
const ai_jobs_service_1 = require("./ai-jobs.service");
const ai_jobs_entity_1 = require("../../../entities/ai-jobs.entity");
const ai_jobs_run_entity_1 = require("../../../entities/ai-jobs-run.entity");
const content_entity_1 = require("../../../entities/content.entity");
const ai_errors_entity_1 = require("../../../entities/ai-errors.entity");
let AiJobsModule = class AiJobsModule {
};
exports.AiJobsModule = AiJobsModule;
exports.AiJobsModule = AiJobsModule = __decorate([
    (0, common_1.Module)({
        imports: [
            typeorm_1.TypeOrmModule.forFeature([ai_jobs_entity_1.AiJob, ai_jobs_run_entity_1.AiJobsRun, content_entity_1.InstaContent, ai_errors_entity_1.AiError]),
            aws_module_1.AwsModule,
            bull_1.BullModule.registerQueue({ name: 'aiJobsQueue' }),
        ],
        controllers: [ai_jobs_controller_1.AiJobsController],
        providers: [ai_jobs_service_1.AiJobsService],
        exports: [ai_jobs_service_1.AiJobsService],
    })
], AiJobsModule);
//# sourceMappingURL=ai-jobs.module.js.map