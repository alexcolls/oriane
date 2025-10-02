import { ConfigService } from '@nestjs/config';
import { AwsOsService } from '../../aws/aws.os.service';
export declare class OpenSearchService {
    private readonly configService;
    private readonly awsOsService;
    private readonly logger;
    private readonly imageModelId;
    private readonly textModelId;
    private readonly embDim;
    private readonly region;
    private bedrockClient;
    constructor(configService: ConfigService, awsOsService: AwsOsService);
    private invokeBedrockModel;
    searchVideosByImage(imageUrl: string, k?: number, numCandidates?: number, platform?: string): Promise<Array<{
        code: string;
        score: number;
    }>>;
    embedImageFromBase64(b64: string): Promise<number[]>;
    embedImageFromUrl(url: string): Promise<number[]>;
    embedImageFromBuffer(buf: Buffer | Uint8Array): Promise<number[]>;
    searchSimilarVideosFromBase64(b64: string, k?: number, numCandidates?: number, platform?: string): Promise<Array<{
        code: string;
        score: number;
    }>>;
    embedText(text: string): Promise<number[]>;
    searchVideosHybrid(queryText: string, size?: number, _numCandidates?: number): Promise<Array<{
        code: string;
        score: number;
    }>>;
    embedMultiModal(text: string, b64Image: string): Promise<number[]>;
}
