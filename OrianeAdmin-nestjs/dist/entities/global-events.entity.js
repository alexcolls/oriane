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
exports.GlobalEvent = void 0;
const typeorm_1 = require("typeorm");
let GlobalEvent = class GlobalEvent {
};
exports.GlobalEvent = GlobalEvent;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('increment', { type: 'bigint' }),
    __metadata("design:type", Number)
], GlobalEvent.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'last_profile_collector_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], GlobalEvent.prototype, "lastProfileCollectorAt", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'last_acquisition_at',
        type: 'timestamp with time zone',
        nullable: false,
        default: () => 'CURRENT_TIMESTAMP',
    }),
    __metadata("design:type", Date)
], GlobalEvent.prototype, "lastAcquisitionAt", void 0);
__decorate([
    (0, typeorm_1.Column)({
        name: 'last_extraction_at',
        type: 'timestamp with time zone',
        nullable: false,
        default: () => 'CURRENT_TIMESTAMP',
    }),
    __metadata("design:type", Date)
], GlobalEvent.prototype, "lastExtractionAt", void 0);
exports.GlobalEvent = GlobalEvent = __decorate([
    (0, typeorm_1.Entity)('global_events')
], GlobalEvent);
//# sourceMappingURL=global-events.entity.js.map