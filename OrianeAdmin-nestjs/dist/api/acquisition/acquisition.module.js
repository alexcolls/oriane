"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AcquisitionModule = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const acquisition_controller_1 = require("./acquisition.controller");
const acquisition_service_1 = require("./acquisition.service");
const aws_module_1 = require("../../aws/aws.module");
const oriane_user_entity_1 = require("../../entities/oriane-user.entity");
const global_events_entity_1 = require("../../entities/global-events.entity");
let AcquisitionModule = class AcquisitionModule {
};
exports.AcquisitionModule = AcquisitionModule;
exports.AcquisitionModule = AcquisitionModule = __decorate([
    (0, common_1.Module)({
        imports: [typeorm_1.TypeOrmModule.forFeature([oriane_user_entity_1.OrianeUser, global_events_entity_1.GlobalEvent]), aws_module_1.AwsModule],
        controllers: [acquisition_controller_1.AcquisitionController],
        providers: [acquisition_service_1.AcquisitionService],
        exports: [acquisition_service_1.AcquisitionService],
    })
], AcquisitionModule);
//# sourceMappingURL=acquisition.module.js.map