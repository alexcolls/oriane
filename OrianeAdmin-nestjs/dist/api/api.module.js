"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ApiModule = void 0;
const common_1 = require("@nestjs/common");
const acquisition_module_1 = require("./acquisition/acquisition.module");
const ai_errors_module_1 = require("./ai/errors/ai-errors.module");
const ai_jobs_module_1 = require("./ai/jobs/ai-jobs.module");
const ai_results_module_1 = require("./ai/results/ai-results.module");
const ai_warnings_module_1 = require("./ai/warnings/ai-warnings.module");
const content_module_1 = require("./content/content.module");
const extraction_module_1 = require("./extraction/extraction.module");
const handles_module_1 = require("./handles/handles.module");
const hiker_api_client_module_1 = require("./hiker-api-client/hiker-api-client.module");
const opensearch_module_1 = require("./opensearch/opensearch.module");
const search_accounts_module_1 = require("./search-accounts/search-accounts.module");
const insta_profiles_module_1 = require("./users/instagram/insta-profiles.module");
let ApiModule = class ApiModule {
};
exports.ApiModule = ApiModule;
exports.ApiModule = ApiModule = __decorate([
    (0, common_1.Module)({
        imports: [
            acquisition_module_1.AcquisitionModule,
            ai_errors_module_1.AiErrorsModule,
            ai_jobs_module_1.AiJobsModule,
            ai_results_module_1.AiResultsModule,
            ai_warnings_module_1.AiWarningsModule,
            content_module_1.ContentModule,
            extraction_module_1.ExtractionModule,
            handles_module_1.HandlesModule,
            hiker_api_client_module_1.HikerApiClientModule,
            opensearch_module_1.OpenSearchModule,
            search_accounts_module_1.SearchAccountsModule,
            insta_profiles_module_1.InstagramProfileModule,
        ],
        controllers: [],
        providers: [],
        exports: [],
    })
], ApiModule);
//# sourceMappingURL=api.module.js.map