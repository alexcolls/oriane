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
var ContentService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContentService = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const axios_1 = require("axios");
const content_entity_1 = require("../../entities/content.entity");
const aws_s3_service_1 = require("../../aws/aws.s3.service");
const hiker_api_client_service_1 = require("../hiker-api-client/hiker-api-client.service");
const utils_1 = require("../../utils");
const oriane_user_entity_1 = require("../../entities/oriane-user.entity");
let ContentService = ContentService_1 = class ContentService {
    constructor(contentRepository, userRepository, hikerApiService, configService, awsS3Service) {
        this.contentRepository = contentRepository;
        this.userRepository = userRepository;
        this.hikerApiService = hikerApiService;
        this.configService = configService;
        this.awsS3Service = awsS3Service;
        this.logger = new common_1.Logger(ContentService_1.name);
    }
    async getAllContent({ content_type, offset, limit, search, }) {
        const query = this.contentRepository.createQueryBuilder('content');
        if (content_type === 'monitored') {
            query.andWhere('content.is_monitored = :monitored', { monitored: true });
        }
        if (content_type === 'watched') {
            query.andWhere('content.is_watched = :watched', { watched: true });
        }
        if (search) {
            query.andWhere('(content.username ILIKE :search OR content.code ILIKE :search)', { search: `%${search}%` });
        }
        const [data, total] = await query
            .orderBy('content.created_at', 'DESC')
            .skip(offset)
            .take(limit)
            .getManyAndCount();
        return {
            data,
            total,
        };
    }
    async refreshContentByCode({ code, }) {
        const mediaData = await this.hikerApiService.getMediaInfoByCode(code);
        const media = mediaData?.media_or_ad;
        if (!media) {
            throw new common_1.HttpException('Invalid content code.', common_1.HttpStatus.NOT_FOUND);
        }
        const content = await this.contentRepository.findOne({
            where: { code },
        });
        if (!content) {
            throw new common_1.HttpException('Content not found.', common_1.HttpStatus.NOT_FOUND);
        }
        await this.contentRepository.update({ code }, {
            caption: media?.caption?.text,
            status: 'active',
            reshareCount: media?.reshare_count,
            igPlayCount: media?.ig_play_count,
            likeCount: media?.like_count,
            commentCount: media?.comment_count,
            updatedAt: new Date(),
        });
        return { success: true, message: 'Content successfully updated' };
    }
    async addMonitoredContent({ url, username, }) {
        const orianeUser = await this.userRepository.findOne({
            where: { username },
        });
        if (!orianeUser) {
            return {
                success: false,
                message: `This handle "${username}" does not exist in Oriane database.`,
            };
        }
        if (!orianeUser.isCreator) {
            return {
                success: false,
                message: `This handle "${username}" exists in the database, but needs to be a Creator or Both role.`,
            };
        }
        const mediaData = await this.hikerApiService?.getMediaInfoByUrl(url);
        if (!mediaData?.media_or_ad?.pk) {
            throw new Error('No valid media found from the provided URL.');
        }
        const mediaOrAd = mediaData.media_or_ad;
        const mediaId = String(mediaOrAd.pk);
        const code = mediaOrAd.code;
        let existingContent = await this.contentRepository.findOne({
            where: { code, isWatched: true },
        });
        if (existingContent) {
            if (existingContent.monitoredBy?.includes(username)) {
                return {
                    success: false,
                    message: `This content is already monitored by ${username}.`,
                };
            }
            existingContent.monitoredBy = Array.from(new Set([...(existingContent.monitoredBy || []), username]));
            existingContent.isMonitored = true;
            existingContent.updatedAt = new Date();
            await this.contentRepository.save(existingContent);
            return {
                success: true,
                message: `Content marked as monitored.`,
            };
        }
        existingContent = await this.contentRepository.findOne({
            where: { code, isMonitored: true },
        });
        if (existingContent) {
            if (existingContent.monitoredBy?.includes(username)) {
                return {
                    success: false,
                    message: `This reel has already been protected by ${username}.`,
                };
            }
            existingContent.monitoredBy = Array.from(new Set([...(existingContent.monitoredBy || []), username]));
            await this.contentRepository.save(existingContent);
            return {
                success: true,
                message: `Content updated: ${username} added as protector.`,
            };
        }
        const downloadImageUrl = mediaOrAd?.image_versions2?.candidates?.[0]?.url;
        const downloadVideoUrl = mediaOrAd?.video_versions?.[0]?.url;
        const [imageBuffer, videoBuffer] = await Promise.all([
            (0, utils_1.downloadBufferFromUrl)(downloadImageUrl),
            (0, utils_1.downloadBufferFromUrl)(downloadVideoUrl),
        ]);
        const awsS3Service = new aws_s3_service_1.AwsS3Service(this.configService);
        await awsS3Service.onModuleInit();
        const imageKey = `instagram/${code}/image.jpg`;
        const videoKey = `instagram/${code}/video.mp4`;
        const [imageS3Url, videoS3Url] = await Promise.all([
            awsS3Service.uploadBufferToS3(imageBuffer, imageKey, 'image/jpeg'),
            awsS3Service.uploadBufferToS3(videoBuffer, videoKey, 'video/mp4'),
        ]);
        const contentToSave = this.contentRepository.create({
            userId: mediaOrAd?.user?.pk || null,
            username: mediaOrAd?.user?.username || '',
            mediaId: mediaId,
            caption: mediaOrAd?.caption?.text || '',
            imageUrl: imageS3Url,
            videoUrl: videoS3Url,
            likeCount: mediaOrAd?.like_count || 0,
            commentCount: mediaOrAd?.comment_count || 0,
            publishDate: new Date(mediaOrAd?.taken_at * 1000),
            updatedAt: new Date(),
            reshareCount: mediaOrAd?.reshare_count || 0,
            igPlayCount: mediaOrAd?.ig_play_count || 0,
            coauthorProducers: mediaOrAd?.coauthor_producers?.map((e) => e?.username) || [],
            status: mediaOrAd?.status || 'Active',
            code: mediaOrAd?.code || '',
            isWatched: false,
            isMonitored: true,
            monitoredBy: [username],
        });
        await this.contentRepository.save(contentToSave);
        return {
            success: true,
            message: 'Content has been successfully protected and monitored.',
        };
    }
    async getImageById({ id }) {
        const content = await this.contentRepository.findOne({
            where: { id },
            select: ['imageUrl'],
        });
        if (!content) {
            throw new common_1.HttpException('Error fetching content: Not found', common_1.HttpStatus.NOT_FOUND);
        }
        const rawUrl = content.imageUrl;
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        const region = this.configService.get('AWS_REGION');
        const expectedPrefix = `https://${bucket}.s3.${region}.amazonaws.com/`;
        let key = rawUrl;
        if (rawUrl.startsWith(expectedPrefix)) {
            key = rawUrl.substring(expectedPrefix.length);
        }
        const signedUrl = await this.awsS3Service.getSignedUrlForKey(key);
        const response = await axios_1.default.get(signedUrl, {
            responseType: 'arraybuffer',
        });
        return response.data;
    }
    async getImageByCode({ code }) {
        return await this.awsS3Service.downloadImageFromS3('instagram', code, 'jpg');
    }
    async getImageUrlById({ id }) {
        const content = await this.contentRepository.findOne({
            where: { id },
            select: ['imageUrl'],
        });
        if (!content) {
            throw new common_1.HttpException('Content not found', common_1.HttpStatus.NOT_FOUND);
        }
        const rawUrl = content.imageUrl;
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        const region = this.configService.get('AWS_REGION');
        const expectedPrefix = `https://${bucket}.s3.${region}.amazonaws.com/`;
        let key = rawUrl;
        if (rawUrl.startsWith(expectedPrefix)) {
            key = rawUrl.substring(expectedPrefix.length);
        }
        await this.awsS3Service.onModuleInit();
        const signedUrl = await this.awsS3Service.getSignedUrlForKey(key);
        return signedUrl;
    }
    async getImageUrlByCode({ code }) {
        const content = await this.contentRepository.findOne({
            where: { code },
            select: ['imageUrl'],
        });
        if (!content) {
            throw new common_1.HttpException('Content not found', common_1.HttpStatus.NOT_FOUND);
        }
        const rawUrl = content.imageUrl;
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        const region = this.configService.get('AWS_REGION');
        const expectedPrefix = `https://${bucket}.s3.${region}.amazonaws.com/`;
        let key = rawUrl;
        if (rawUrl.startsWith(expectedPrefix)) {
            key = rawUrl.substring(expectedPrefix.length);
        }
        await this.awsS3Service.onModuleInit();
        const signedUrl = await this.awsS3Service.getSignedUrlForKey(key);
        return signedUrl;
    }
    async getVideoById({ id }) {
        const content = await this.contentRepository.findOne({
            where: { id },
            select: ['videoUrl'],
        });
        if (!content) {
            throw new common_1.HttpException('Content not found', common_1.HttpStatus.NOT_FOUND);
        }
        const rawUrl = content.videoUrl;
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        const region = this.configService.get('AWS_REGION');
        const expectedPrefix = `https://${bucket}.s3.${region}.amazonaws.com/`;
        let key = rawUrl;
        if (rawUrl.startsWith(expectedPrefix)) {
            key = rawUrl.substring(expectedPrefix.length);
        }
        const signedUrl = await this.awsS3Service.getSignedUrlForKey(key);
        const response = await axios_1.default.get(signedUrl, {
            responseType: 'arraybuffer',
        });
        return response.data;
    }
    async getVideoByCode({ code }) {
        const content = await this.contentRepository.findOne({
            where: { code },
            select: ['videoUrl'],
        });
        if (!content) {
            throw new common_1.HttpException('Content not found', common_1.HttpStatus.NOT_FOUND);
        }
        const rawUrl = content.videoUrl;
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        const region = this.configService.get('AWS_REGION');
        const expectedPrefix = `https://${bucket}.s3.${region}.amazonaws.com/`;
        let key = rawUrl;
        if (rawUrl.startsWith(expectedPrefix)) {
            key = rawUrl.substring(expectedPrefix.length);
        }
        const signedUrl = await this.awsS3Service.getSignedUrlForKey(key);
        const response = await axios_1.default.get(signedUrl, {
            responseType: 'arraybuffer',
        });
        return response.data;
    }
    async getVideoUrlById({ id }) {
        const content = await this.contentRepository.findOne({
            where: { id },
            select: ['videoUrl'],
        });
        if (!content) {
            throw new common_1.HttpException('Content not found', common_1.HttpStatus.NOT_FOUND);
        }
        const rawUrl = content.videoUrl;
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        const region = this.configService.get('AWS_REGION');
        const expectedPrefix = `https://${bucket}.s3.${region}.amazonaws.com/`;
        let key = rawUrl;
        if (rawUrl.startsWith(expectedPrefix)) {
            key = rawUrl.substring(expectedPrefix.length);
        }
        const signedUrl = await this.awsS3Service.getSignedUrlForKey(key);
        return signedUrl;
    }
    async getVideoUrlByCode({ code }) {
        const content = await this.contentRepository.findOne({
            where: { code },
            select: ['videoUrl'],
        });
        if (!content) {
            throw new common_1.HttpException('Content not found', common_1.HttpStatus.NOT_FOUND);
        }
        const rawUrl = content.videoUrl;
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        const region = this.configService.get('AWS_REGION');
        const expectedPrefix = `https://${bucket}.s3.${region}.amazonaws.com/`;
        let key = rawUrl;
        if (rawUrl.startsWith(expectedPrefix)) {
            key = rawUrl.substring(expectedPrefix.length);
        }
        const signedUrl = await this.awsS3Service.getSignedUrlForKey(key);
        return signedUrl;
    }
    async getPublishDateByCode({ code, }) {
        const content = await this.contentRepository.findOne({
            where: { code },
            select: ['publishDate'],
        });
        return content ? content.publishDate : null;
    }
    async getFramesImage({ code, frameNumber, platform = 'instagram', extension = 'jpg', }) {
        try {
            const key = `${platform}/${code}/frames/${frameNumber}.${extension}`;
            const signedUrl = await this.awsS3Service.getSignedUrlForKey(key);
            return signedUrl;
        }
        catch (error) {
            this.logger.error(`Error getting frame image for code ${code}, frame ${frameNumber}: ${error.message}`);
            throw new common_1.HttpException('Frame image not found', common_1.HttpStatus.NOT_FOUND);
        }
    }
    async deleteContent({ code }) {
        const result = await this.contentRepository.delete({ code });
        if (result.affected === 0) {
            throw new common_1.HttpException('Error deleting content: Content not found', common_1.HttpStatus.NOT_FOUND);
        }
    }
    async deleteContentById({ id }) {
        const result = await this.contentRepository.delete({ id });
        if (result.affected === 0) {
            throw new common_1.HttpException('Error deleting content: Content not found', common_1.HttpStatus.NOT_FOUND);
        }
    }
    async getContentCount() {
        try {
            const count = await this.contentRepository.count();
            return count;
        }
        catch (error) {
            console.error('Error fetching content count:', error);
            throw new common_1.HttpException('Error fetching content count', common_1.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    async getMonitoredContentCount() {
        try {
            const count = await this.contentRepository.count({
                where: { isMonitored: true },
            });
            return count;
        }
        catch (error) {
            console.error('Error fetching monitored content count:', error);
            throw new common_1.HttpException('Error fetching content count', common_1.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    async getWatchedContentCount() {
        try {
            const count = await this.contentRepository.count({
                where: { isWatched: true },
            });
            return count;
        }
        catch (error) {
            console.error('Error fetching watched content count:', error);
            throw new common_1.HttpException('Error fetching content count', common_1.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    async getDownloadedVideosCount() {
        try {
            const count = await this.contentRepository.count({
                where: { isDownloaded: true },
            });
            return count;
        }
        catch (error) {
            console.error('Error fetching downloaded videos count:', error);
            throw new common_1.HttpException('Error fetching content count', common_1.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    async getExtractedVideosCount() {
        try {
            const count = await this.contentRepository.count({
                where: { isExtracted: true },
            });
            return count;
        }
        catch (error) {
            console.error('Error fetching extracted videos count:', error);
            throw new common_1.HttpException('Error fetching content count', common_1.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
};
exports.ContentService = ContentService;
exports.ContentService = ContentService = ContentService_1 = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(content_entity_1.InstaContent)),
    __param(1, (0, typeorm_1.InjectRepository)(oriane_user_entity_1.OrianeUser)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        typeorm_2.Repository,
        hiker_api_client_service_1.HikerApiClientService,
        config_1.ConfigService,
        aws_s3_service_1.AwsS3Service])
], ContentService);
//# sourceMappingURL=content.service.js.map