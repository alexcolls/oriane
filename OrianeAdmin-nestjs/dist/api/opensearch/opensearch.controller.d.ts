import { AwsOsService } from '../../aws/aws.os.service';
import { OpenSearchService } from './opensearch.service';
import { SearchVideosHybridQueryDto, SearchVideosByUrlQueryDto, SearchVideosByBase64BodyDto, SearchVideosByBase64QueryDto } from './dto/opensearch-query.dto';
export declare class OpenSearchController {
    private readonly openSearchService;
    private readonly awsOsService;
    private readonly logger;
    constructor(openSearchService: OpenSearchService, awsOsService: AwsOsService);
    searchVideosHybrid(queryDto: SearchVideosHybridQueryDto): Promise<{
        code: string;
        score: number;
    }[]>;
    getFramesForVideo(videoOsId: string): Promise<any[]>;
    searchVideosByImageUrl(queryDto: SearchVideosByUrlQueryDto): Promise<{
        code: string;
        score: number;
    }[]>;
    searchVideosByImageBase64(bodyDto: SearchVideosByBase64BodyDto, queryDto: SearchVideosByBase64QueryDto): Promise<{
        code: string;
        score: number;
    }[]>;
    getEmbeddingForText(text: string): Promise<number[]>;
}
