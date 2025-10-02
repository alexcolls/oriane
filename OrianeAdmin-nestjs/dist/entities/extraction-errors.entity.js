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
exports.ExtractionError = void 0;
const typeorm_1 = require("typeorm");
let ExtractionError = class ExtractionError {
};
exports.ExtractionError = ExtractionError;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], ExtractionError.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({
        name: 'created_at',
        type: 'timestamp with time zone',
        default: () => 'CURRENT_TIMESTAMP',
        nullable: false,
    }),
    __metadata("design:type", Date)
], ExtractionError.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.Index)(),
    (0, typeorm_1.Column)({ type: 'varchar', name: 'code', nullable: false }),
    __metadata("design:type", String)
], ExtractionError.prototype, "code", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'text', name: 'error', nullable: false }),
    __metadata("design:type", String)
], ExtractionError.prototype, "error", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)('InstaContent', 'errors', {
        nullable: false,
    }),
    (0, typeorm_1.JoinColumn)({ name: 'code', referencedColumnName: 'code' }),
    __metadata("design:type", Object)
], ExtractionError.prototype, "relatedContent", void 0);
exports.ExtractionError = ExtractionError = __decorate([
    (0, typeorm_1.Entity)('extraction_errors')
], ExtractionError);
//# sourceMappingURL=extraction-errors.entity.js.map