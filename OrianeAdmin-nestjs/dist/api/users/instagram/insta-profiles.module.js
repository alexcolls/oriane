"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.InstagramProfileModule = void 0;
const common_1 = require("@nestjs/common");
const insta_profiles_controller_1 = require("./insta-profiles.controller");
const insta_profiles_service_1 = require("./insta-profiles.service");
const profile_collector_controller_1 = require("./profile-collector.controller");
const profile_collector_service_1 = require("./profile-collector.service");
const typeorm_1 = require("@nestjs/typeorm");
const insta_profiles_entity_1 = require("../../../entities/insta-profiles.entity");
const oriane_user_entity_1 = require("../../../entities/oriane-user.entity");
const hiker_api_client_module_1 = require("../../hiker-api-client/hiker-api-client.module");
let InstagramProfileModule = class InstagramProfileModule {
};
exports.InstagramProfileModule = InstagramProfileModule;
exports.InstagramProfileModule = InstagramProfileModule = __decorate([
    (0, common_1.Module)({
        imports: [
            typeorm_1.TypeOrmModule.forFeature([insta_profiles_entity_1.InstaProfile, oriane_user_entity_1.OrianeUser]),
            hiker_api_client_module_1.HikerApiClientModule,
        ],
        controllers: [insta_profiles_controller_1.InstaProfilesController, profile_collector_controller_1.ProfileCollectorController],
        providers: [insta_profiles_service_1.InstaProfilesService, profile_collector_service_1.ProfileCollectorService],
        exports: [insta_profiles_service_1.InstaProfilesService, profile_collector_service_1.ProfileCollectorService],
    })
], InstagramProfileModule);
//# sourceMappingURL=insta-profiles.module.js.map