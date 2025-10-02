import { AiResultsService } from './ai-results.service';
import { AiResult } from '../../../entities/ai-results.entity';
import { GetAiResultsQueryDto, GetAiMatchesCountQueryDto, CreateAiResultDto, UpdateAiResultDto, PaginatedAiResultsResponseDto } from './dto/ai-results.dto';
export declare class AiResultsController {
    private readonly aiResultsService;
    constructor(aiResultsService: AiResultsService);
    getAiResults(queryDto: GetAiResultsQueryDto): Promise<PaginatedAiResultsResponseDto>;
    getAiMatches(queryDto: GetAiResultsQueryDto): Promise<PaginatedAiResultsResponseDto>;
    getAiMatchesCountByJobId(jobId: string, queryDto: GetAiMatchesCountQueryDto): Promise<{
        matches: number;
    }>;
    getAiResultById(id: string): Promise<AiResult>;
    createAiResult(createAiResultDto: CreateAiResultDto): Promise<AiResult>;
    updateAiResult(id: string, updateAiResultDto: UpdateAiResultDto): Promise<AiResult>;
    deleteAiResult(id: string): Promise<void>;
}
