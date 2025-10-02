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
exports.InstaContent = void 0;
const typeorm_1 = require("typeorm");
const extraction_errors_entity_1 = require("./extraction-errors.entity");
const insta_profiles_entity_1 = require("./insta-profiles.entity");
let InstaContent = class InstaContent {
};
exports.InstaContent = InstaContent;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], InstaContent.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'varchar',
        length: 255,
        name: 'media_id',
        nullable: false,
        unique: true,
    }),
    __metadata("design:type", String)
], InstaContent.prototype, "mediaId", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 255, name: 'user_id', nullable: false }),
    __metadata("design:type", String)
], InstaContent.prototype, "userId", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => insta_profiles_entity_1.InstaProfile, (profile) => profile.contents, {
        nullable: true,
    }),
    (0, typeorm_1.JoinColumn)({ name: 'user_id', referencedColumnName: 'userId' }),
    __metadata("design:type", insta_profiles_entity_1.InstaProfile)
], InstaContent.prototype, "instaProfile", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_insta_content_username_trgm', { synchronize: false }),
    (0, typeorm_1.Column)({ type: 'varchar', length: 255, name: 'username', nullable: false }),
    __metadata("design:type", String)
], InstaContent.prototype, "username", void 0);
__decorate([
    (0, typeorm_1.Column)({
        type: 'varchar',
        length: 50,
        name: 'status',
        nullable: true,
        default: 'active',
    }),
    __metadata("design:type", String)
], InstaContent.prototype, "status", void 0);
__decorate([
    (0, typeorm_1.Index)('insta_content_code_key', { unique: true }),
    (0, typeorm_1.Column)({ type: 'varchar', length: 255, name: 'code', nullable: false }),
    __metadata("design:type", String)
], InstaContent.prototype, "code", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_insta_content_caption_trgm', { synchronize: false }),
    (0, typeorm_1.Column)({ type: 'text', name: 'caption', nullable: true }),
    __metadata("design:type", String)
], InstaContent.prototype, "caption", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_insta_content_created_at'),
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], InstaContent.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_insta_content_publish_date'),
    (0, typeorm_1.Column)({
        name: 'publish_date',
        type: 'timestamp with time zone',
        nullable: false,
    }),
    __metadata("design:type", Date)
], InstaContent.prototype, "publishDate", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_insta_content_is_monitored'),
    (0, typeorm_1.Column)({
        name: 'is_monitored',
        type: 'boolean',
        nullable: true,
        default: false,
    }),
    __metadata("design:type", Boolean)
], InstaContent.prototype, "isMonitored", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_insta_content_is_watched'),
    (0, typeorm_1.Column)({
        name: 'is_watched',
        type: 'boolean',
        nullable: true,
        default: false,
    }),
    __metadata("design:type", Boolean)
], InstaContent.prototype, "isWatched", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'ig_play_count',
        type: 'integer',
        nullable: true,
        default: 0,
    }),
    __metadata("design:type", Number)
], InstaContent.prototype, "igPlayCount", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'reshare_count',
        type: 'integer',
        nullable: true,
        default: 0,
    }),
    __metadata("design:type", Number)
], InstaContent.prototype, "reshareCount", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'comment_count',
        type: 'integer',
        nullable: true,
        default: 0,
    }),
    __metadata("design:type", Number)
], InstaContent.prototype, "commentCount", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'like_count', type: 'integer', nullable: true, default: 0 }),
    __metadata("design:type", Number)
], InstaContent.prototype, "likeCount", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'video_url', type: 'varchar', nullable: true }),
    __metadata("design:type", String)
], InstaContent.prototype, "videoUrl", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_insta_content_is_extracted'),
    (0, typeorm_1.Column)({
        name: 'is_extracted',
        type: 'boolean',
        nullable: true,
        default: false,
    }),
    __metadata("design:type", Boolean)
], InstaContent.prototype, "isExtracted", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'is_removed',
        type: 'boolean',
        nullable: true,
        default: false,
    }),
    __metadata("design:type", Boolean)
], InstaContent.prototype, "isRemoved", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'image_url', type: 'varchar', nullable: true }),
    __metadata("design:type", String)
], InstaContent.prototype, "imageUrl", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'coauthor_producers',
        type: 'text',
        array: true,
        nullable: true,
        default: () => "'{}'",
    }),
    __metadata("design:type", Array)
], InstaContent.prototype, "coauthorProducers", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'last_refreshed_at',
        type: 'timestamp with time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], InstaContent.prototype, "lastRefreshedAt", void 0);
__decorate([
    (0, typeorm_1.UpdateDateColumn)({
        name: 'updated_at',
        type: 'timestamp with time zone',
        nullable: true,
        default: () => 'CURRENT_TIMESTAMP',
    }),
    __metadata("design:type", Date)
], InstaContent.prototype, "updatedAt", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_insta_content_monitored_by_trgm', { synchronize: false }),
    (0, typeorm_1.Column)({
        name: 'monitored_by',
        type: 'text',
        array: true,
        nullable: true,
        default: () => "'{}'",
    }),
    __metadata("design:type", Array)
], InstaContent.prototype, "monitoredBy", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'search_text', type: 'text', nullable: true }),
    __metadata("design:type", String)
], InstaContent.prototype, "searchText", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'is_downloaded',
        type: 'boolean',
        nullable: false,
        default: true,
    }),
    __metadata("design:type", Boolean)
], InstaContent.prototype, "isDownloaded", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'duration', type: 'real', nullable: true }),
    __metadata("design:type", Number)
], InstaContent.prototype, "duration", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'is_embedded',
        type: 'boolean',
        nullable: false,
        default: false,
    }),
    __metadata("design:type", Boolean)
], InstaContent.prototype, "isEmbedded", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'frames', type: 'integer', nullable: true }),
    __metadata("design:type", Number)
], InstaContent.prototype, "frames", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'is_cropped',
        type: 'boolean',
        nullable: true,
        default: false,
    }),
    __metadata("design:type", Boolean)
], InstaContent.prototype, "isCropped", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => extraction_errors_entity_1.ExtractionError, (errorLog) => errorLog.relatedContent),
    __metadata("design:type", Array)
], InstaContent.prototype, "errors", void 0);
exports.InstaContent = InstaContent = __decorate([
    (0, typeorm_1.Entity)('insta_content'),
    (0, typeorm_1.Index)('insta_content_caption_trgm_idx', { synchronize: false }),
    (0, typeorm_1.Index)('insta_content_username_trgm_idx', { synchronize: false }),
    (0, typeorm_1.Index)('idx_insta_content_monitored_by_trgm', { synchronize: false }),
    (0, typeorm_1.Index)('idx_insta_content_code_trgm', { synchronize: false })
], InstaContent);
//# sourceMappingURL=content.entity.js.map