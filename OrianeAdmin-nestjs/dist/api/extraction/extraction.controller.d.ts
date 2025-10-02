import { AwsOsService } from '../../aws/aws.os.service';
import { ExtractionService } from './extraction.service';
export declare class ExtractionController {
    private readonly extractionService;
    private readonly awsOsService;
    private readonly logger;
    constructor(extractionService: ExtractionService, awsOsService: AwsOsService);
    extractAllVideos(): Promise<{
        message: string;
        totalEligible: number;
        dispatched: number;
    }>;
    extractFramesByCode(code: string): Promise<{
        status: string;
        message: string;
    }>;
    getExtractionProgress(): Promise<{
        total: number;
        downloaded: number;
        extracted: number;
        embedded: number;
        downloadProgress: number;
        extractionProgress: number;
        embeddingsProgress: number;
    }>;
    getLastExtractionTimestamp(): Promise<string>;
    verifyExtractionByCode(code: string): Promise<boolean>;
    verifyEmbeddingStatus(code: string): Promise<{
        code: string;
        isEmbedded: boolean;
        exists: boolean;
    }>;
    countVideos(): Promise<{
        count: number;
    }>;
}
