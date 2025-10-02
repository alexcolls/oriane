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
var ContentController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContentController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const content_service_1 = require("./content.service");
const get_all_content_dto_1 = require("./dto/get-all-content.dto");
const add_monitored_content_dto_1 = require("./dto/add-monitored-content.dto");
let ContentController = ContentController_1 = class ContentController {
    constructor(contentService) {
        this.contentService = contentService;
        this.logger = new common_1.Logger(ContentController_1.name);
    }
    async getAllContent(query) {
        return this.contentService.getAllContent(query);
    }
    async getContentCount() {
        return this.contentService.getContentCount();
    }
    async getMonitoredContentCount() {
        return this.contentService.getMonitoredContentCount();
    }
    async getWatchedContentCount() {
        return this.contentService.getWatchedContentCount();
    }
    async getDownloadedVideosCount() {
        return await this.contentService.getDownloadedVideosCount();
    }
    async getExtractedVideosCount() {
        return await this.contentService.getExtractedVideosCount();
    }
    async addMonitoredContent(addMonitoredContentDto) {
        return this.contentService.addMonitoredContent(addMonitoredContentDto);
    }
    async refreshContentByCode(code) {
        const refreshContentByCodeDto = { code };
        return await this.contentService.refreshContentByCode(refreshContentByCodeDto);
    }
    async getPortraitImage(id_code) {
        if (id_code.length > 22) {
            const mediaFetchByIdDto = { id: id_code };
            return await this.contentService.getImageById(mediaFetchByIdDto);
        }
        else {
            const mediaFetchByCodeDto = { code: id_code };
            return await this.contentService.getImageByCode(mediaFetchByCodeDto);
        }
    }
    async getImageUrl(id_code) {
        if (id_code.length > 22) {
            const mediaFetchByIdDto = { id: id_code };
            return await this.contentService.getImageUrlById(mediaFetchByIdDto);
        }
        else {
            const mediaFetchByCodeDto = { code: id_code };
            return await this.contentService.getImageUrlByCode(mediaFetchByCodeDto);
        }
    }
    async getVideo(id_code) {
        if (id_code.length > 28) {
            const mediaFetchByIdDto = { id: id_code };
            return await this.contentService.getVideoById(mediaFetchByIdDto);
        }
        else {
            const mediaFetchByCodeDto = { code: id_code };
            return await this.contentService.getVideoByCode(mediaFetchByCodeDto);
        }
    }
    async getVideoUrl(id_code) {
        if (id_code.length > 28) {
            const mediaFetchByIdDto = { id: id_code };
            return await this.contentService.getVideoUrlById(mediaFetchByIdDto);
        }
        else {
            const mediaFetchByCodeDto = { code: id_code };
            return await this.contentService.getVideoUrlByCode(mediaFetchByCodeDto);
        }
    }
    async getPublishDateByCode(code) {
        const mediaFetchByCodeDto = { code };
        return await this.contentService.getPublishDateByCode(mediaFetchByCodeDto);
    }
    async getFramesImage(code, frame_number) {
        const getFramesImageDto = {
            code,
            frameNumber: frame_number,
        };
        return await this.contentService.getFramesImage(getFramesImageDto);
    }
    async deleteContent(code) {
        const mediaFetchByCodeDto = { code };
        return await this.contentService.deleteContent(mediaFetchByCodeDto);
    }
    async deleteContentById(id) {
        const mediaFetchByIdDto = { id };
        return await this.contentService.deleteContentById(mediaFetchByIdDto);
    }
};
exports.ContentController = ContentController;
__decorate([
    (0, common_1.Get)('all'),
    __param(0, (0, common_1.Query)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [get_all_content_dto_1.GetAllContentDto]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getAllContent", null);
__decorate([
    (0, common_1.Get)('all/count'),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getContentCount", null);
__decorate([
    (0, common_1.Get)('all/monitored/count'),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getMonitoredContentCount", null);
__decorate([
    (0, common_1.Get)('all/watched/count'),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getWatchedContentCount", null);
__decorate([
    (0, common_1.Get)('all/downloaded/count'),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getDownloadedVideosCount", null);
__decorate([
    (0, common_1.Get)('all/extracted/count'),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getExtractedVideosCount", null);
__decorate([
    (0, common_1.Post)('add-monitored-content'),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [add_monitored_content_dto_1.AddMonitoredContentDto]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "addMonitoredContent", null);
__decorate([
    (0, common_1.Get)('refresh-content/:code'),
    __param(0, (0, common_1.Param)('code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "refreshContentByCode", null);
__decorate([
    (0, common_1.Get)('get-image/buffer/:id_code'),
    __param(0, (0, common_1.Param)('id_code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getPortraitImage", null);
__decorate([
    (0, common_1.Get)('get-image/url/:id_code'),
    __param(0, (0, common_1.Param)('id_code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getImageUrl", null);
__decorate([
    (0, common_1.Get)('get-video/buffer/:id_code'),
    __param(0, (0, common_1.Param)('id_code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getVideo", null);
__decorate([
    (0, common_1.Get)('get-video/url/:id_code'),
    __param(0, (0, common_1.Param)('id_code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getVideoUrl", null);
__decorate([
    (0, common_1.Get)('get-published-date/:code'),
    __param(0, (0, common_1.Param)('code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getPublishDateByCode", null);
__decorate([
    (0, common_1.Get)('get-frames-image/:code/:frame_number'),
    __param(0, (0, common_1.Param)('code')),
    __param(1, (0, common_1.Param)('frame_number', common_1.ParseIntPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Number]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "getFramesImage", null);
__decorate([
    (0, common_1.Delete)('code/:code'),
    __param(0, (0, common_1.Param)('code')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "deleteContent", null);
__decorate([
    (0, common_1.Delete)('id/:id'),
    __param(0, (0, common_1.Param)('id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", Promise)
], ContentController.prototype, "deleteContentById", null);
exports.ContentController = ContentController = ContentController_1 = __decorate([
    (0, swagger_1.ApiTags)('Instagram Contents'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('content'),
    __metadata("design:paramtypes", [content_service_1.ContentService])
], ContentController);
//# sourceMappingURL=content.controller.js.map