import { ConfigService } from '@nestjs/config';
import { Repository } from 'typeorm';
import { InstaContent } from '../../entities/content.entity';
import { GlobalEvent } from '../../entities/global-events.entity';
import { DatabaseService } from '../../database/database.service';
export declare class ExtractionService {
    private readonly instaContentRepository;
    private readonly globalEventRepository;
    private readonly configService;
    private readonly databaseService;
    private readonly logger;
    private readonly GLOBAL_EVENT_ID;
    constructor(instaContentRepository: Repository<InstaContent>, globalEventRepository: Repository<GlobalEvent>, configService: ConfigService, databaseService: DatabaseService);
    private codeExists;
    private alreadyEmbedded;
    checkEmbeddingStatus(code: string): Promise<{
        code: string;
        isEmbedded: boolean;
        exists: boolean;
    }>;
    verifyFramesExtractionByCode(code: string): Promise<boolean>;
    getExtractionProgress(): Promise<{
        total: number;
        downloaded: number;
        extracted: number;
        embedded: number;
        downloadProgress: number;
        extractionProgress: number;
        embeddingsProgress: number;
    }>;
    getLastExtractionTimestamp(): Promise<string | null>;
    private updateLastExtractionTimestamp;
    extractVideoByCode(code: string): Promise<{
        status: string;
        message: string;
    }>;
    extractAllVideos(): Promise<{
        message: string;
        totalEligible: number;
        dispatched: number;
    }>;
}
