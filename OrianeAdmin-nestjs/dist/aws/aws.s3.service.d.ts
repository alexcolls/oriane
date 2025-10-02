import { OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
export declare class AwsS3Service implements OnModuleInit {
    private configService;
    private s3Client;
    private readonly logger;
    private debug;
    constructor(configService: ConfigService);
    onModuleInit(): Promise<void>;
    private streamToBuffer;
    downloadVideoFromS3(platform: string, code: string, extension?: string): Promise<Buffer>;
    downloadImageFromS3(platform: string, code: string, extension?: string): Promise<Buffer>;
    getSignedUrlForKey(key: string, expiresIn?: number): Promise<string>;
    uploadBufferToS3(buffer: Buffer, key: string, contentType: string): Promise<string>;
}
