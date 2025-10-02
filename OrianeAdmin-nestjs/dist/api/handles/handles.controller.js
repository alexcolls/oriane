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
var HandlesController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.HandlesController = void 0;
const common_1 = require("@nestjs/common");
const platform_express_1 = require("@nestjs/platform-express");
const swagger_1 = require("@nestjs/swagger");
const handles_service_1 = require("./handles.service");
const file_logging_interceptor_1 = require("../../interceptors/file-logging.interceptor");
const oriane_user_entity_1 = require("../../entities/oriane-user.entity");
const handle_dto_1 = require("./dto/handle.dto");
let HandlesController = HandlesController_1 = class HandlesController {
    constructor(handlesService) {
        this.handlesService = handlesService;
        this.logger = new common_1.Logger(HandlesController_1.name);
    }
    async addUser(addUserDto) {
        return this.handlesService.addUser(addUserDto.username, addUserDto.priority, addUserDto.environment);
    }
    async addWatchedHandle(addWatchedDto) {
        return this.handlesService.addWatchedHandle(addWatchedDto.username);
    }
    async uploadCSV(file) {
        this.logger.log(`Received file in controller: ${file?.originalname || 'No file received'}`);
        if (!file) {
            this.logger.error('No file uploaded by client');
            throw new common_1.BadRequestException('No file uploaded.');
        }
        return this.handlesService.uploadCSV(file);
    }
    async testSqs() {
        this.logger.log('Testing SQS connection...');
        try {
            await this.handlesService.testSqsConnection();
            return { success: true, message: 'SQS connection test successful' };
        }
        catch (error) {
            this.logger.error('SQS connection test failed:', error);
            return { success: false, message: `SQS connection test failed: ${error.message}` };
        }
    }
    async updateHandle(currentUsername, updates) {
        return this.handlesService.updateHandle(currentUsername, updates);
    }
    async deactivateHandle(dto) {
        return this.handlesService.deactivateHandle(dto.username);
    }
    async activateHandle(dto) {
        return this.handlesService.activateHandle(dto.username);
    }
    async getHandles(queryDto) {
        let parsedFilters = undefined;
        if (queryDto.filters) {
            try {
                parsedFilters = JSON.parse(queryDto.filters);
            }
            catch (e) {
                this.logger.warn(`Could not parse 'filters' query parameter: ${queryDto.filters}. Error: ${e.message}`);
            }
        }
        return this.handlesService.getHandles(queryDto.environment || '', queryDto.user_type, queryDto.offset, queryDto.limit, queryDto.search, parsedFilters);
    }
    async getHandleByUsername(username) {
        return this.handlesService.getHandleByUsername(username);
    }
    async getHandlesVideoCodes(queryDto) {
        return this.handlesService.getVideoCodesByUsername(queryDto.user_type, queryDto.offset ?? 0, queryDto.limit ?? 500, queryDto.search);
    }
    async getAllVideoCodes(queryDto) {
        return this.handlesService.getAllVideoCodes(queryDto.user_type);
    }
};
exports.HandlesController = HandlesController;
__decorate([
    (0, common_1.Post)('add-user'),
    (0, swagger_1.ApiOperation)({ summary: 'Add a new Oriane user (typically a creator)' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.CREATED,
        description: 'User successfully added.',
        type: oriane_user_entity_1.OrianeUser,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.CONFLICT,
        description: 'User already exists.',
    }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [handle_dto_1.AddUserDto]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "addUser", null);
__decorate([
    (0, common_1.Post)('add-watched'),
    (0, swagger_1.ApiOperation)({ summary: 'Add a new watched handle' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.CREATED,
        description: 'Watched handle successfully added.',
        type: oriane_user_entity_1.OrianeUser,
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.CONFLICT,
        description: 'User already exists.',
    }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [handle_dto_1.AddWatchedHandleDto]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "addWatchedHandle", null);
__decorate([
    (0, common_1.Post)('upload'),
    (0, swagger_1.ApiOperation)({
        summary: 'Upload a CSV file with usernames to add as watched handles',
    }),
    (0, swagger_1.ApiConsumes)('multipart/form-data'),
    (0, swagger_1.ApiBody)({
        schema: {
            type: 'object',
            properties: { file: { type: 'string', format: 'binary' } },
            required: ['file'],
        },
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'CSV received and processing started in background.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'No file uploaded or invalid file.',
    }),
    (0, common_1.UseInterceptors)((0, platform_express_1.FileInterceptor)('file'), file_logging_interceptor_1.FileLoggingInterceptor),
    __param(0, (0, common_1.UploadedFile)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "uploadCSV", null);
__decorate([
    (0, common_1.Post)('test-sqs'),
    (0, swagger_1.ApiOperation)({ summary: 'Test SQS connection' }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "testSqs", null);
__decorate([
    (0, common_1.Patch)('update'),
    (0, swagger_1.ApiOperation)({ summary: 'Update an existing handle' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Handle successfully updated.',
        type: oriane_user_entity_1.OrianeUser,
    }),
    (0, swagger_1.ApiResponse)({ status: common_1.HttpStatus.NOT_FOUND, description: 'User not found.' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input.',
    }),
    (0, swagger_1.ApiBody)({
        schema: {
            type: 'object',
            properties: {
                currentUsername: { type: 'string', example: 'old_username' },
                updates: {
                    type: 'object',
                    properties: {
                        username: {
                            type: 'string',
                            example: 'new_username',
                            nullable: true,
                        },
                        priority: {
                            type: 'string',
                            enum: ['low', 'medium', 'high'],
                            nullable: true,
                        },
                        isCreator: { type: 'boolean', nullable: true },
                        isWatched: { type: 'boolean', nullable: true },
                    },
                },
            },
            required: ['currentUsername', 'updates'],
        },
    }),
    __param(0, (0, common_1.Body)('currentUsername')),
    __param(1, (0, common_1.Body)('updates', common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, handle_dto_1.UpdateHandlePayloadDto]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "updateHandle", null);
__decorate([
    (0, common_1.Patch)('deactivate'),
    (0, swagger_1.ApiOperation)({ summary: 'Deactivate a handle by username' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Handle successfully deactivated.',
        type: oriane_user_entity_1.OrianeUser,
    }),
    (0, swagger_1.ApiResponse)({ status: common_1.HttpStatus.NOT_FOUND, description: 'User not found.' }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [handle_dto_1.DeactivateHandleDto]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "deactivateHandle", null);
__decorate([
    (0, common_1.Patch)('activate'),
    (0, swagger_1.ApiOperation)({ summary: 'Activate a handle by username' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Handle successfully activated.',
        type: oriane_user_entity_1.OrianeUser,
    }),
    (0, swagger_1.ApiResponse)({ status: common_1.HttpStatus.NOT_FOUND, description: 'User not found.' }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [handle_dto_1.ActivateHandleDto]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "activateHandle", null);
__decorate([
    (0, common_1.Get)('all'),
    (0, swagger_1.ApiOperation)({
        summary: 'Get handles with pagination, filtering, and search',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Handles retrieved successfully.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input.',
    }),
    __param(0, (0, common_1.Query)(new common_1.ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
    }))),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [handle_dto_1.GetHandlesQueryDto]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "getHandles", null);
__decorate([
    (0, common_1.Get)(':username'),
    (0, swagger_1.ApiOperation)({ summary: 'Get a specific handle by username' }),
    (0, swagger_1.ApiParam)({
        name: 'username',
        description: 'Username of the handle to retrieve',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Handle retrieved successfully.',
        type: oriane_user_entity_1.OrianeUser,
    }),
    (0, swagger_1.ApiResponse)({ status: common_1.HttpStatus.NOT_FOUND, description: 'User not found.' }),
    __param(0, (0, common_1.Param)('username')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "getHandleByUsername", null);
__decorate([
    (0, common_1.Get)('video-codes-by-username'),
    (0, swagger_1.ApiOperation)({ summary: 'Get video codes grouped by usernames' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'Video codes retrieved successfully.',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid input.',
    }),
    __param(0, (0, common_1.Query)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [handle_dto_1.GetVideoCodesQueryDto]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "getHandlesVideoCodes", null);
__decorate([
    (0, common_1.Get)('all-video-codes'),
    (0, swagger_1.ApiOperation)({ summary: 'Get all video codes for a specific user type' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.OK,
        description: 'List of all video codes.',
        type: [String],
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Invalid user_type.',
    }),
    __param(0, (0, common_1.Query)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [handle_dto_1.GetAllVideoCodesQueryDto]),
    __metadata("design:returntype", Promise)
], HandlesController.prototype, "getAllVideoCodes", null);
exports.HandlesController = HandlesController = HandlesController_1 = __decorate([
    (0, swagger_1.ApiTags)('Handles'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('handles'),
    __metadata("design:paramtypes", [handles_service_1.HandlesService])
], HandlesController);
//# sourceMappingURL=handles.controller.js.map