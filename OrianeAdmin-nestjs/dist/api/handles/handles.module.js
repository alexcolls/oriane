"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.HandlesModule = void 0;
const common_1 = require("@nestjs/common");
const handles_controller_1 = require("./handles.controller");
const handles_service_1 = require("./handles.service");
const typeorm_1 = require("@nestjs/typeorm");
const oriane_user_entity_1 = require("../../entities/oriane-user.entity");
const content_entity_1 = require("../../entities/content.entity");
const insta_profiles_entity_1 = require("../../entities/insta-profiles.entity");
const insta_profiles_module_1 = require("../users/instagram/insta-profiles.module");
const handle_scheduler_controller_1 = require("./handle-scheduler.controller");
const handle_scheduler_service_1 = require("./handle-scheduler.service");
const aws_module_1 = require("../../aws/aws.module");
let HandlesModule = class HandlesModule {
};
exports.HandlesModule = HandlesModule;
exports.HandlesModule = HandlesModule = __decorate([
    (0, common_1.Module)({
        imports: [
            typeorm_1.TypeOrmModule.forFeature([oriane_user_entity_1.OrianeUser, content_entity_1.InstaContent, insta_profiles_entity_1.InstaProfile]),
            insta_profiles_module_1.InstagramProfileModule,
            aws_module_1.AwsModule,
        ],
        controllers: [handles_controller_1.HandlesController, handle_scheduler_controller_1.HandleSchedulerController],
        providers: [handles_service_1.HandlesService, handle_scheduler_service_1.HandleSchedulerService],
        exports: [handles_service_1.HandlesService, handle_scheduler_service_1.HandleSchedulerService],
    })
], HandlesModule);
//# sourceMappingURL=handles.module.js.map