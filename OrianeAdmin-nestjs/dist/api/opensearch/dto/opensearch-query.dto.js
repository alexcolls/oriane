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
exports.SearchVideosByBase64QueryDto = exports.SearchVideosByBase64BodyDto = exports.SearchVideosByUrlQueryDto = exports.SearchVideosHybridQueryDto = void 0;
const swagger_1 = require("@nestjs/swagger");
const class_validator_1 = require("class-validator");
const class_transformer_1 = require("class-transformer");
class SearchVideosHybridQueryDto {
    constructor() {
        this.size = 10;
        this.num_candidates = 100;
    }
}
exports.SearchVideosHybridQueryDto = SearchVideosHybridQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Text query for hybrid search.',
        example: 'sunset over mountains',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], SearchVideosHybridQueryDto.prototype, "q", void 0);
__decorate([
    (0, swagger_1.ApiPropertyOptional)({
        description: 'Number of results to return (acts as k for k-NN).',
        default: 10,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    (0, class_validator_1.Max)(100),
    __metadata("design:type", Number)
], SearchVideosHybridQueryDto.prototype, "size", void 0);
__decorate([
    (0, swagger_1.ApiPropertyOptional)({
        description: 'Number of candidates for k-NN search.',
        default: 100,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], SearchVideosHybridQueryDto.prototype, "num_candidates", void 0);
class SearchVideosByUrlQueryDto {
    constructor() {
        this.k = 10;
        this.numCandidates = 100;
    }
}
exports.SearchVideosByUrlQueryDto = SearchVideosByUrlQueryDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Public URL of the image to search with.',
        example: 'https://example.com/image.jpg',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    __metadata("design:type", String)
], SearchVideosByUrlQueryDto.prototype, "url", void 0);
__decorate([
    (0, swagger_1.ApiPropertyOptional)({
        description: 'Number of similar results to return.',
        default: 10,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    (0, class_validator_1.Max)(50),
    __metadata("design:type", Number)
], SearchVideosByUrlQueryDto.prototype, "k", void 0);
__decorate([
    (0, swagger_1.ApiPropertyOptional)({
        description: 'Number of candidates for k-NN search.',
        default: 100,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], SearchVideosByUrlQueryDto.prototype, "numCandidates", void 0);
__decorate([
    (0, swagger_1.ApiPropertyOptional)({
        description: 'Filter by platform (e.g., instagram).',
        example: 'instagram',
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], SearchVideosByUrlQueryDto.prototype, "platform", void 0);
class SearchVideosByBase64BodyDto {
}
exports.SearchVideosByBase64BodyDto = SearchVideosByBase64BodyDto;
__decorate([
    (0, swagger_1.ApiProperty)({
        description: 'Base64 encoded image data.',
        example: 'iVBORw0KGgoAAAANSUhEUgAAAAUA...',
    }),
    (0, class_validator_1.IsString)(),
    (0, class_validator_1.IsNotEmpty)(),
    (0, class_validator_1.IsBase64)(),
    __metadata("design:type", String)
], SearchVideosByBase64BodyDto.prototype, "b64", void 0);
class SearchVideosByBase64QueryDto {
    constructor() {
        this.k = 10;
        this.numCandidates = 100;
    }
}
exports.SearchVideosByBase64QueryDto = SearchVideosByBase64QueryDto;
__decorate([
    (0, swagger_1.ApiPropertyOptional)({
        description: 'Number of similar results to return.',
        default: 10,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    (0, class_validator_1.Max)(50),
    __metadata("design:type", Number)
], SearchVideosByBase64QueryDto.prototype, "k", void 0);
__decorate([
    (0, swagger_1.ApiPropertyOptional)({
        description: 'Number of candidates for k-NN search.',
        default: 100,
        type: Number,
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_transformer_1.Type)(() => Number),
    (0, class_validator_1.IsInt)(),
    (0, class_validator_1.Min)(1),
    __metadata("design:type", Number)
], SearchVideosByBase64QueryDto.prototype, "numCandidates", void 0);
__decorate([
    (0, swagger_1.ApiPropertyOptional)({
        description: 'Filter by platform (e.g., instagram).',
        example: 'instagram',
    }),
    (0, class_validator_1.IsOptional)(),
    (0, class_validator_1.IsString)(),
    __metadata("design:type", String)
], SearchVideosByBase64QueryDto.prototype, "platform", void 0);
//# sourceMappingURL=opensearch-query.dto.js.map