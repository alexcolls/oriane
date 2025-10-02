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
exports.OrianeUser = void 0;
const typeorm_1 = require("typeorm");
const insta_profiles_entity_1 = require("./insta-profiles.entity");
let OrianeUser = class OrianeUser {
};
exports.OrianeUser = OrianeUser;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], OrianeUser.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'next_check_at',
        type: 'timestamp with time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], OrianeUser.prototype, "nextCheckAt", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'check_frequency', type: 'integer', nullable: false }),
    __metadata("design:type", Number)
], OrianeUser.prototype, "checkFrequency", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'priority',
        type: 'varchar',
        nullable: true,
        default: 'medium',
    }),
    __metadata("design:type", String)
], OrianeUser.prototype, "priority", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'environment', type: 'text', nullable: false }),
    __metadata("design:type", String)
], OrianeUser.prototype, "environment", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'last_cursor',
        type: 'timestamp with time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], OrianeUser.prototype, "lastCursor", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'last_checked',
        type: 'timestamp with time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], OrianeUser.prototype, "lastChecked", void 0);
__decorate([
    (0, typeorm_1.Index)('unique_username', { unique: true }),
    (0, typeorm_1.Index)('idx_username_oriane_users'),
    (0, typeorm_1.Column)({ name: 'username', type: 'text', nullable: false }),
    __metadata("design:type", String)
], OrianeUser.prototype, "username", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_is_creator_oriane_users', { synchronize: false }),
    (0, typeorm_1.Column)({
        name: 'is_creator',
        type: 'boolean',
        nullable: false,
        default: false,
    }),
    __metadata("design:type", Boolean)
], OrianeUser.prototype, "isCreator", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_oriane_users_is_deactivated'),
    (0, typeorm_1.Column)({
        name: 'is_deactivated',
        type: 'boolean',
        nullable: true,
        default: false,
    }),
    __metadata("design:type", Boolean)
], OrianeUser.prototype, "isDeactivated", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'state_error',
        type: 'boolean',
        nullable: true,
        default: false,
    }),
    __metadata("design:type", Boolean)
], OrianeUser.prototype, "stateError", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'account_status',
        type: 'varchar',
        length: 20,
        nullable: true,
        default: 'not checked',
    }),
    __metadata("design:type", String)
], OrianeUser.prototype, "accountStatus", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'error_message', type: 'text', nullable: true }),
    __metadata("design:type", String)
], OrianeUser.prototype, "errorMessage", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_oriane_users_is_watched'),
    (0, typeorm_1.Column)({
        name: 'is_watched',
        type: 'boolean',
        nullable: false,
        default: false,
    }),
    __metadata("design:type", Boolean)
], OrianeUser.prototype, "isWatched", void 0);
__decorate([
    (0, typeorm_1.Index)('idx_oriane_users_first_fetched'),
    (0, typeorm_1.Column)({
        name: 'first_fetched',
        type: 'timestamp with time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], OrianeUser.prototype, "firstFetched", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
    }),
    __metadata("design:type", Date)
], OrianeUser.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'last_fetched',
        type: 'timestamp with time zone',
        nullable: true,
    }),
    __metadata("design:type", Date)
], OrianeUser.prototype, "lastFetched", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => insta_profiles_entity_1.InstaProfile, (instaProfile) => instaProfile.orianeUser),
    __metadata("design:type", Array)
], OrianeUser.prototype, "instaProfiles", void 0);
exports.OrianeUser = OrianeUser = __decorate([
    (0, typeorm_1.Entity)('oriane_users')
], OrianeUser);
//# sourceMappingURL=oriane-user.entity.js.map