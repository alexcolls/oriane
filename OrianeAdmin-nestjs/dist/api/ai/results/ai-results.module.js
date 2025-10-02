"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AiResultsModule = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const ai_results_controller_1 = require("./ai-results.controller");
const ai_results_service_1 = require("./ai-results.service");
const database_module_1 = require("../../../database/database.module");
const ai_results_entity_1 = require("../../../entities/ai-results.entity");
let AiResultsModule = class AiResultsModule {
};
exports.AiResultsModule = AiResultsModule;
exports.AiResultsModule = AiResultsModule = __decorate([
    (0, common_1.Module)({
        imports: [typeorm_1.TypeOrmModule.forFeature([ai_results_entity_1.AiResult]), database_module_1.DatabaseModule],
        controllers: [ai_results_controller_1.AiResultsController],
        providers: [ai_results_service_1.AiResultsService],
        exports: [ai_results_service_1.AiResultsService],
    })
], AiResultsModule);
//# sourceMappingURL=ai-results.module.js.map