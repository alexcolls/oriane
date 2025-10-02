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
var AwsS3Service_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AwsS3Service = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const client_s3_1 = require("@aws-sdk/client-s3");
const s3_request_presigner_1 = require("@aws-sdk/s3-request-presigner");
let AwsS3Service = AwsS3Service_1 = class AwsS3Service {
    constructor(configService) {
        this.configService = configService;
        this.logger = new common_1.Logger(AwsS3Service_1.name);
        this.debug = false;
    }
    async onModuleInit() {
        const region = this.configService.get('AWS_REGION');
        const accessKeyId = this.configService.get('AWS_ACCESS_KEY_ID');
        const secretAccessKey = this.configService.get('AWS_SECRET_ACCESS_KEY');
        if (!region || !accessKeyId || !secretAccessKey) {
            throw new Error('Missing required AWS configuration. Please check your environment variables.');
        }
        this.s3Client = new client_s3_1.S3Client({
            region,
            credentials: {
                accessKeyId,
                secretAccessKey,
            },
        });
        if (this.debug) {
            this.logger.log('AWS S3 client initialized successfully');
        }
    }
    async streamToBuffer(stream) {
        return new Promise((resolve, reject) => {
            const chunks = [];
            stream.on('data', (chunk) => chunks.push(chunk));
            stream.on('error', reject);
            stream.on('end', () => resolve(Buffer.concat(chunks)));
        });
    }
    async downloadVideoFromS3(platform, code, extension = 'mp4') {
        const key = `${platform}/${code}/video.${extension}`;
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        if (!bucket) {
            throw new Error('Missing AWS_S3_VIDEOS_BUCKET configuration.');
        }
        try {
            const command = new client_s3_1.GetObjectCommand({
                Bucket: bucket,
                Key: key,
            });
            const response = await this.s3Client.send(command);
            const stream = response.Body;
            if (this.debug) {
                this.logger.log(`Successfully downloaded video from S3: ${key}`);
            }
            return await this.streamToBuffer(stream);
        }
        catch (error) {
            this.logger.error(`Error downloading video from S3: ${key}`, error);
            throw error;
        }
    }
    async downloadImageFromS3(platform, code, extension = 'jpg') {
        const key = `${platform}/${code}/image.${extension}`;
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        if (!bucket) {
            throw new Error('Missing AWS_S3_VIDEOS_BUCKET configuration.');
        }
        try {
            const command = new client_s3_1.GetObjectCommand({
                Bucket: bucket,
                Key: key,
            });
            const response = await this.s3Client.send(command);
            const stream = response.Body;
            if (this.debug) {
                this.logger.log(`Successfully downloaded image from S3: ${key}`);
            }
            return await this.streamToBuffer(stream);
        }
        catch (error) {
            this.logger.error(`Error downloading image from S3: ${key}`, error);
            throw error;
        }
    }
    async getSignedUrlForKey(key, expiresIn = 3600) {
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        if (!bucket) {
            throw new Error('Missing AWS_S3_VIDEOS_BUCKET configuration.');
        }
        try {
            const command = new client_s3_1.GetObjectCommand({
                Bucket: bucket,
                Key: key,
            });
            const signedUrl = await (0, s3_request_presigner_1.getSignedUrl)(this.s3Client, command, {
                expiresIn,
            });
            if (this.debug) {
                this.logger.log(`Generated signed URL for key: ${key}`);
            }
            return signedUrl;
        }
        catch (error) {
            this.logger.error(`Error generating signed URL for key: ${key}`, error);
            throw error;
        }
    }
    async uploadBufferToS3(buffer, key, contentType) {
        const bucket = this.configService.get('AWS_S3_VIDEOS_BUCKET');
        if (!bucket) {
            throw new Error('Missing AWS_S3_VIDEOS_BUCKET configuration.');
        }
        const { PutObjectCommand } = await Promise.resolve().then(() => require('@aws-sdk/client-s3'));
        const command = new PutObjectCommand({
            Bucket: bucket,
            Key: key,
            Body: buffer,
            ContentType: contentType,
        });
        await this.s3Client.send(command);
        const region = this.configService.get('AWS_REGION');
        return `https://${bucket}.s3.${region}.amazonaws.com/${key}`;
    }
};
exports.AwsS3Service = AwsS3Service;
exports.AwsS3Service = AwsS3Service = AwsS3Service_1 = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [config_1.ConfigService])
], AwsS3Service);
//# sourceMappingURL=aws.s3.service.js.map