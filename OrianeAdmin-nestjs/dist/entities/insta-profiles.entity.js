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
exports.InstaProfile = void 0;
const typeorm_1 = require("typeorm");
const content_entity_1 = require("./content.entity");
const oriane_user_entity_1 = require("./oriane-user.entity");
let InstaProfile = class InstaProfile {
};
exports.InstaProfile = InstaProfile;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], InstaProfile.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Index)('insta_profiles_username_key', { unique: true }),
    (0, typeorm_1.Column)({ type: 'varchar', length: 255, name: 'username', nullable: false }),
    __metadata("design:type", String)
], InstaProfile.prototype, "username", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 255, name: 'platform', nullable: true }),
    __metadata("design:type", String)
], InstaProfile.prototype, "platform", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'boolean', name: 'is_verified', nullable: true }),
    __metadata("design:type", Boolean)
], InstaProfile.prototype, "isVerified", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'text', nullable: true }),
    __metadata("design:type", String)
], InstaProfile.prototype, "biography", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'profile_pic', type: 'text', nullable: true }),
    __metadata("design:type", String)
], InstaProfile.prototype, "profilePic", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'followers_count', type: 'integer', nullable: true }),
    __metadata("design:type", Number)
], InstaProfile.prototype, "followersCount", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'following_count', type: 'integer', nullable: true }),
    __metadata("design:type", Number)
], InstaProfile.prototype, "followingCount", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp without time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], InstaProfile.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.UpdateDateColumn)({
        name: 'updated_at',
        type: 'timestamp without time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], InstaProfile.prototype, "updatedAt", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'engagement_rate', type: 'double precision', nullable: true }),
    __metadata("design:type", Number)
], InstaProfile.prototype, "engagementRate", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'average_likes', type: 'integer', nullable: true }),
    __metadata("design:type", Number)
], InstaProfile.prototype, "averageLikes", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'average_comments', type: 'integer', nullable: true }),
    __metadata("design:type", Number)
], InstaProfile.prototype, "averageComments", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'account_type',
        type: 'varchar',
        length: 255,
        nullable: true,
    }),
    __metadata("design:type", String)
], InstaProfile.prototype, "accountType", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'is_business_account', type: 'boolean', nullable: true }),
    __metadata("design:type", Boolean)
], InstaProfile.prototype, "isBusinessAccount", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'category', type: 'varchar', length: 255, nullable: true }),
    __metadata("design:type", String)
], InstaProfile.prototype, "category", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'external_url', type: 'text', nullable: true }),
    __metadata("design:type", String)
], InstaProfile.prototype, "externalUrl", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'public_email',
        type: 'varchar',
        length: 255,
        nullable: true,
    }),
    __metadata("design:type", String)
], InstaProfile.prototype, "publicEmail", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'last_post_date',
        type: 'timestamp without time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], InstaProfile.prototype, "lastPostDate", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'account_ref', type: 'varchar', length: 255, nullable: true }),
    __metadata("design:type", String)
], InstaProfile.prototype, "accountRef", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'last_updated',
        type: 'timestamp without time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], InstaProfile.prototype, "lastUpdated", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'is_tracked', type: 'boolean', nullable: true }),
    __metadata("design:type", Boolean)
], InstaProfile.prototype, "isTracked", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'is_onboarded', type: 'boolean', nullable: true }),
    __metadata("design:type", Boolean)
], InstaProfile.prototype, "isOnboarded", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'full_name', type: 'varchar', length: 255, nullable: true }),
    __metadata("design:type", String)
], InstaProfile.prototype, "fullName", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'is_private', type: 'boolean', nullable: true }),
    __metadata("design:type", Boolean)
], InstaProfile.prototype, "isPrivate", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'media_count', type: 'integer', nullable: true }),
    __metadata("design:type", Number)
], InstaProfile.prototype, "mediaCount", void 0);
__decorate([
    (0, typeorm_1.Index)('insta_profiles_oriane_user_id_key', { unique: true }),
    (0, typeorm_1.Column)({ name: 'oriane_user_id', type: 'uuid', nullable: true }),
    __metadata("design:type", String)
], InstaProfile.prototype, "orianeUserId", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => oriane_user_entity_1.OrianeUser, (orianeUser) => orianeUser.instaProfiles, {
        onDelete: 'CASCADE',
        nullable: true,
    }),
    (0, typeorm_1.JoinColumn)({ name: 'oriane_user_id' }),
    __metadata("design:type", oriane_user_entity_1.OrianeUser)
], InstaProfile.prototype, "orianeUser", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_insta_profiles_user_id'),
    (0, typeorm_1.Index)('insta_profiles_user_id_key', { unique: true }),
    (0, typeorm_1.Column)({ name: 'user_id', type: 'varchar', nullable: true }),
    __metadata("design:type", String)
], InstaProfile.prototype, "userId", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => content_entity_1.InstaContent, (content) => content.instaProfile),
    __metadata("design:type", Array)
], InstaProfile.prototype, "contents", void 0);
exports.InstaProfile = InstaProfile = __decorate([
    (0, typeorm_1.Entity)('insta_profiles')
], InstaProfile);
//# sourceMappingURL=insta-profiles.entity.js.map