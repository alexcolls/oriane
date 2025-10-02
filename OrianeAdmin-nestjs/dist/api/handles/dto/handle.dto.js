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
Object.defineProperty(exports, "__esModule", { value: true });
exports.GetAllVideoCodesQueryDto = exports.GetVideoCodesQueryDto = exports.GetHandlesQueryDto = exports.ActivateHandleDto = exports.DeactivateHandleDto = exports.UpdateHandleDto = exports.UpdateHandlePayloadDto = exports.AddWatchedHandleDto = exports.AddUserDto = void 0;
const swagger_1 = require("@nestjs/swagger");
const class_validator_1 = require("class-validator");
const class_transformer_1 = require("class-transformer");
class AddUserDto {
}
exports.AddUserDto = AddUserDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'john_doe',
        description: 'Username of the user to add',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], AddUserDto.prototype, "username", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'medium',
        enum: ['low', 'medium', 'high'],
        description: 'Priority for the user',
    }),
    (0, class_validator_1.IsEnum)(['low', 'medium', 'high']),
    __metadata("design:type", String)
], AddUserDto.prototype, "priority", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'production',
        description: 'Environment for the user (optional)',
        required: false,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], AddUserDto.prototype, "environment", void 0);
class AddWatchedHandleDto {
}
exports.AddWatchedHandleDto = AddWatchedHandleDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'jane_doe',
        description: 'Username of the watched handle to add',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], AddWatchedHandleDto.prototype, "username", void 0);
class UpdateHandlePayloadDto {
}
exports.UpdateHandlePayloadDto = UpdateHandlePayloadDto;
__decorate([
    (0, swagger_1.ApiProperty)({ example: 'new_username', required: false }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], UpdateHandlePayloadDto.prototype, "username", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'high',
        enum: ['low', 'medium', 'high'],
        required: false,
    }),
    (0, class_validator_1.IsEnum)(['low', 'medium', 'high']),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], UpdateHandlePayloadDto.prototype, "priority", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ example: true, required: false }),
    (0, class_validator_1.IsBoolean)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Boolean)
], UpdateHandlePayloadDto.prototype, "isCreator", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ example: true, required: false }),
    (0, class_validator_1.IsBoolean)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Boolean)
], UpdateHandlePayloadDto.prototype, "isWatched", void 0);
class UpdateHandleDto {
}
exports.UpdateHandleDto = UpdateHandleDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'current_username',
        description: 'The current username of the handle to update',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], UpdateHandleDto.prototype, "currentUsername", void 0);
class DeactivateHandleDto {
}
exports.DeactivateHandleDto = DeactivateHandleDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'user_to_deactivate',
        description: 'Username of the handle to deactivate',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], DeactivateHandleDto.prototype, "username", void 0);
class ActivateHandleDto {
}
exports.ActivateHandleDto = ActivateHandleDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'user_to_activate',
        description: 'Username of the handle to activate',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], ActivateHandleDto.prototype, "username", void 0);
class GetHandlesQueryDto {
    constructor() {
        this.user_type = 'users';
        this.offset = 0;
        this.limit = 50;
    }
}
exports.GetHandlesQueryDto = GetHandlesQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        required: false,
        description: 'Environment filter (optional - if not provided, searches all environments)',
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], GetHandlesQueryDto.prototype, "environment", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        required: false,
        default: 'users',
        enum: ['users', 'watched'],
        description: "'users' for creators, 'watched' for watched users",
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsEnum)(['users', 'watched']),
    __metadata("design:type", String)
], GetHandlesQueryDto.prototype, "user_type", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        required: false,
        default: 0,
        type: Number,
        description: 'Offset for pagination',
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], GetHandlesQueryDto.prototype, "offset", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        required: false,
        default: 50,
        type: Number,
        description: 'Limit for pagination',
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], GetHandlesQueryDto.prototype, "limit", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ required: false, description: 'Search term for username' }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], GetHandlesQueryDto.prototype, "search", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'JSON string of ApiFilter[] or leave for service to handle undefined',
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], GetHandlesQueryDto.prototype, "filters", void 0);
class GetVideoCodesQueryDto {
    constructor() {
        this.offset = 0;
        this.limit = 50;
    }
}
exports.GetVideoCodesQueryDto = GetVideoCodesQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        enum: ['users', 'watched'],
        description: "'users' for creators, 'watched' for watched users",
    }),
    (0, class_validator_1.IsEnum)(['users', 'watched']),
    __metadata("design:type", String)
], GetVideoCodesQueryDto.prototype, "user_type", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        required: false,
        default: 0,
        type: Number,
        description: 'Offset for pagination of username groups',
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], GetVideoCodesQueryDto.prototype, "offset", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        required: false,
        default: 50,
        type: Number,
        description: 'Limit for pagination of username groups',
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], GetVideoCodesQueryDto.prototype, "limit", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({ required: false, description: 'Search term for username' }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], GetVideoCodesQueryDto.prototype, "search", void 0);
class GetAllVideoCodesQueryDto {
}
exports.GetAllVideoCodesQueryDto = GetAllVideoCodesQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        enum: ['users', 'watched'],
        description: "'users' for creators, 'watched' for watched users",
    }),
    (0, class_validator_1.IsEnum)(['users', 'watched']),
    __metadata("design:type", String)
], GetAllVideoCodesQueryDto.prototype, "user_type", void 0);
//# sourceMappingURL=handle.dto.js.map