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
exports.InstaProfileResponseDto = exports.GetInstaProfilesQueryDto = exports.UpdateInstaProfileDto = exports.CreateInstaProfileDto = void 0;
const swagger_1 = require("@nestjs/swagger");
const class_validator_1 = require("class-validator");
class CreateInstaProfileDto {
}
exports.CreateInstaProfileDto = CreateInstaProfileDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'new_ig_user',
        description: 'Instagram username (must be unique)',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "username", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'instagram',
        description: 'Platform identifier',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "platform", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: false,
        description: 'Is the account verified?',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsBoolean)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Boolean)
], CreateInstaProfileDto.prototype, "isVerified", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'Bio of the user.',
        description: 'User biography',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "biography", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'https://example.com/pic.jpg',
        description: 'URL to profile picture',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsUrl)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "profilePic", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 1000,
        description: 'Number of followers',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Number)
], CreateInstaProfileDto.prototype, "followersCount", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 100,
        description: 'Number of accounts followed',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Number)
], CreateInstaProfileDto.prototype, "followingCount", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 0.05,
        description: 'Engagement rate',
        required: false,
        nullable: true,
        type: 'number',
        format: 'double',
    }),
    (0, class_validator_1.IsNumber)(),
    (0, class_validator_1.Min)(0),
    (0, class_validator_1.Max)(1),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Number)
], CreateInstaProfileDto.prototype, "engagementRate", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 150,
        description: 'Average likes per post',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Number)
], CreateInstaProfileDto.prototype, "averageLikes", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 10,
        description: 'Average comments per post',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Number)
], CreateInstaProfileDto.prototype, "averageComments", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'CREATOR',
        description: 'Type of account',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "accountType", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: true,
        description: 'Is it a business account?',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsBoolean)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Boolean)
], CreateInstaProfileDto.prototype, "isBusinessAccount", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'Art',
        description: 'Category of the account',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "category", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'https://linktr.ee/user',
        description: 'External URL in bio',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsUrl)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "externalUrl", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'user@example.com',
        description: 'Public email address',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsEmail)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "publicEmail", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: '2023-01-15T10:00:00Z',
        description: 'Date of the last post',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsDateString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Date)
], CreateInstaProfileDto.prototype, "lastPostDate", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'ref123',
        description: 'Internal account reference',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "accountRef", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: true,
        description: 'Is this profile being tracked?',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsBoolean)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Boolean)
], CreateInstaProfileDto.prototype, "isTracked", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: false,
        description: 'Has this profile been onboarded?',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsBoolean)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Boolean)
], CreateInstaProfileDto.prototype, "isOnboarded", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 'John Doe',
        description: 'Full name of the user',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "fullName", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: false,
        description: 'Is the account private?',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsBoolean)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Boolean)
], CreateInstaProfileDto.prototype, "isPrivate", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        example: 50,
        description: 'Total media count',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", Number)
], CreateInstaProfileDto.prototype, "mediaCount", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Associated OrianeUser ID (UUID).',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsUUID)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "orianeUserId", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Platform specific User ID.',
        required: false,
        nullable: true,
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsOptional)(),
    __metadata("design:type", String)
], CreateInstaProfileDto.prototype, "userId", void 0);
class UpdateInstaProfileDto extends (0, swagger_1.PartialType)(CreateInstaProfileDto) {
}
exports.UpdateInstaProfileDto = UpdateInstaProfileDto;
const class_transformer_1 = require("class-transformer");
class GetInstaProfilesQueryDto {
    constructor() {
        this.offset = 0;
        this.limit = 10;
    }
}
exports.GetInstaProfilesQueryDto = GetInstaProfilesQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: "Filter by 'isCreator' status. (Note: 'isCreator' is not on InstaProfile entity, this might need adjustment based on where this data lives, e.g., linked OrianeUser)",
        required: false,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsBoolean)(),
    (0, class_transformer_1.Type)(() => Boolean),
    __metadata("design:type", Boolean)
], GetInstaProfilesQueryDto.prototype, "isCreator", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Number of records to skip.',
        required: false,
        default: 0,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(0),
    __metadata("design:type", Number)
], GetInstaProfilesQueryDto.prototype, "offset", void 0);
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Maximum number of records to return.',
        required: false,
        default: 10,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], GetInstaProfilesQueryDto.prototype, "limit", void 0);
const swagger_2 = require("@nestjs/swagger");
const insta_profiles_entity_1 = require("../../../../entities/insta-profiles.entity");
class InstaProfileResponseDto extends (0, swagger_2.OmitType)(insta_profiles_entity_1.InstaProfile, [
    'orianeUser',
    'contents',
]) {
}
exports.InstaProfileResponseDto = InstaProfileResponseDto;
//# sourceMappingURL=insta-profile.dto.js.map