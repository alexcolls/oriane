"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtractionModule = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const config_1 = require("@nestjs/config");
const extraction_controller_1 = require("./extraction.controller");
const extraction_service_1 = require("./extraction.service");
const content_entity_1 = require("../../entities/content.entity");
const global_events_entity_1 = require("../../entities/global-events.entity");
const aws_module_1 = require("../../aws/aws.module");
const database_module_1 = require("../../database/database.module");
let ExtractionModule = class ExtractionModule {
};
exports.ExtractionModule = ExtractionModule;
exports.ExtractionModule = ExtractionModule = __decorate([
    (0, common_1.Module)({
        imports: [
            typeorm_1.TypeOrmModule.forFeature([content_entity_1.InstaContent, global_events_entity_1.GlobalEvent]),
            config_1.ConfigModule,
            aws_module_1.AwsModule,
            database_module_1.DatabaseModule,
        ],
        controllers: [extraction_controller_1.ExtractionController],
        providers: [extraction_service_1.ExtractionService],
        exports: [extraction_service_1.ExtractionService],
    })
], ExtractionModule);
//# sourceMappingURL=extraction.module.js.map