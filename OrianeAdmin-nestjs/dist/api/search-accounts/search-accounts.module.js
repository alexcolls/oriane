"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.SearchAccountsModule = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const aws_module_1 = require("../../aws/aws.module");
const search_accounts_controller_1 = require("./search-accounts.controller");
const search_accounts_service_1 = require("./search-accounts.service");
const search_accounts_job_processor_1 = require("./search-accounts-job.processor");
const oriane_user_entity_1 = require("../../entities/oriane-user.entity");
const insta_profiles_entity_1 = require("../../entities/insta-profiles.entity");
const search_account_job_entity_1 = require("../../entities/search-account-job.entity");
const search_account_result_entity_1 = require("../../entities/search-account-result.entity");
const hiker_api_client_module_1 = require("../hiker-api-client/hiker-api-client.module");
let SearchAccountsModule = class SearchAccountsModule {
};
exports.SearchAccountsModule = SearchAccountsModule;
exports.SearchAccountsModule = SearchAccountsModule = __decorate([
    (0, common_1.Module)({
        imports: [
            typeorm_1.TypeOrmModule.forFeature([
                oriane_user_entity_1.OrianeUser,
                insta_profiles_entity_1.InstaProfile,
                search_account_job_entity_1.SearchAccountJob,
                search_account_result_entity_1.SearchAccountResult,
            ]),
            aws_module_1.AwsModule,
            hiker_api_client_module_1.HikerApiClientModule,
        ],
        controllers: [search_accounts_controller_1.SearchAccountsController],
        providers: [search_accounts_service_1.SearchAccountsService, search_accounts_job_processor_1.SearchAccountsJobProcessor],
        exports: [search_accounts_service_1.SearchAccountsService],
    })
], SearchAccountsModule);
//# sourceMappingURL=search-accounts.module.js.map