"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.DatabaseModule = void 0;
const fs = require("fs");
const path_1 = require("path");
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const config_1 = require("@nestjs/config");
const database_service_1 = require("./database.service");
const oriane_user_entity_1 = require("../entities/oriane-user.entity");
const insta_profiles_entity_1 = require("../entities/insta-profiles.entity");
const content_entity_1 = require("../entities/content.entity");
const global_events_entity_1 = require("../entities/global-events.entity");
const extraction_errors_entity_1 = require("../entities/extraction-errors.entity");
const ai_errors_entity_1 = require("../entities/ai-errors.entity");
const ai_warnings_entity_1 = require("../entities/ai-warnings.entity");
const ai_jobs_entity_1 = require("../entities/ai-jobs.entity");
const ai_jobs_run_entity_1 = require("../entities/ai-jobs-run.entity");
const ai_results_entity_1 = require("../entities/ai-results.entity");
const search_account_job_entity_1 = require("../entities/search-account-job.entity");
const search_account_result_entity_1 = require("../entities/search-account-result.entity");
let DatabaseModule = class DatabaseModule {
};
exports.DatabaseModule = DatabaseModule;
exports.DatabaseModule = DatabaseModule = __decorate([
    (0, common_1.Global)(),
    (0, common_1.Module)({
        imports: [
            config_1.ConfigModule.forRoot(),
            typeorm_1.TypeOrmModule.forRootAsync({
                imports: [config_1.ConfigModule],
                inject: [config_1.ConfigService],
                useFactory: (configService) => ({
                    type: 'postgres',
                    host: configService.get('DB_HOST'),
                    port: +configService.get('DB_PORT'),
                    username: configService.get('DB_USER'),
                    password: configService.get('DB_PASSWORD'),
                    database: configService.get('DB_NAME'),
                    entities: [
                        oriane_user_entity_1.OrianeUser,
                        insta_profiles_entity_1.InstaProfile,
                        content_entity_1.InstaContent,
                        global_events_entity_1.GlobalEvent,
                        extraction_errors_entity_1.ExtractionError,
                        ai_errors_entity_1.AiError,
                        ai_warnings_entity_1.AiWarning,
                        ai_jobs_entity_1.AiJob,
                        ai_jobs_run_entity_1.AiJobsRun,
                        ai_results_entity_1.AiResult,
                        search_account_job_entity_1.SearchAccountJob,
                        search_account_result_entity_1.SearchAccountResult,
                    ],
                    synchronize: false,
                    ssl: configService.get('NODE_ENV') === 'production'
                        ? {
                            rejectUnauthorized: true,
                            ca: fs
                                .readFileSync((0, path_1.join)(__dirname, '../../certs/aws-rds-global.pem'))
                                .toString(),
                        }
                        : {
                            rejectUnauthorized: false,
                        },
                }),
            }),
        ],
        providers: [database_service_1.DatabaseService],
        exports: [database_service_1.DatabaseService, typeorm_1.TypeOrmModule],
    })
], DatabaseModule);
//# sourceMappingURL=database.module.js.map