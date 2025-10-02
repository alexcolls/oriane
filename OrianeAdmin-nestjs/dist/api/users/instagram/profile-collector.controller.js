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
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
var ProfileCollectorController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProfileCollectorController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const profile_collector_service_1 = require("./profile-collector.service");
const profile_collector_dto_1 = require("./dto/profile-collector.dto");
let ProfileCollectorController = ProfileCollectorController_1 = class ProfileCollectorController {
    constructor(profileCollectorService) {
        this.profileCollectorService = profileCollectorService;
        this.logger = new common_1.Logger(ProfileCollectorController_1.name);
    }
    async collectUserProfile(queryDto) {
        this.logger.log(`Request to collect profile for username: ${queryDto.username}`);
        const success = await this.profileCollectorService.collectProfile(queryDto.username);
        if (success) {
            return {
                success: true,
                message: `Profile collection for '${queryDto.username}' completed successfully.`,
            };
        }
        else {
            return {
                success: false,
                message: `Profile collection for '${queryDto.username}' failed (see logs for details, though an exception should have been thrown).`,
            };
        }
    }
};
exports.ProfileCollectorController = ProfileCollectorController;
__decorate([
    (0, common_1.Post)('collect'),
    (0, swagger_1.ApiOperation)({
        summary: 'Trigger profile collection for a specific username.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Profile collection successful.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.NOT_FOUND,
        description: 'User or profile not found by Hiker API or internal OrianeUser record missing.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.INTERNAL_SERVER_ERROR,
        description: 'Internal server error during collection.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input (e.g., missing username).',
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [profile_collector_dto_1.CollectProfileQueryDto]),
    __metadata("design:returntype", Promise)
], ProfileCollectorController.prototype, "collectUserProfile", null);
exports.ProfileCollectorController = ProfileCollectorController = ProfileCollectorController_1 = __decorate([
    (0, swagger_1.ApiTags)('Tasks - Profile Collector'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('profiles'),
    __metadata("design:paramtypes", [profile_collector_service_1.ProfileCollectorService])
], ProfileCollectorController);
//# sourceMappingURL=profile-collector.controller.js.map