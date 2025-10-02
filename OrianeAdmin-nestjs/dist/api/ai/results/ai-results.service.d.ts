import { Repository } from 'typeorm';
import { AiResult } from '../../../entities/ai-results.entity';
import { DatabaseService } from '../../../database/database.service';
type AiResultPostPayload = Omit<AiResult, 'id' | 'createdAt' | 'aiJob' | 'aiJobsRun'>;
export declare class AiResultsService {
    private readonly aiResultRepository;
    private readonly databaseService;
    private readonly logger;
    constructor(aiResultRepository: Repository<AiResult>, databaseService: DatabaseService);
    getAiResults(offset: number, limit: number, order?: 'asc' | 'desc' | null, sortBy?: string | null, search?: string | null): Promise<{
        data: AiResult[];
        total: number;
    }>;
    getAiMatches(offset: number, limit: number, order?: 'asc' | 'desc' | null, sortBy?: string | null, search?: string | null): Promise<{
        data: AiResult[];
        total: number;
    }>;
    getAiMatchesCountByJobId(jobId: string, threshold: number): Promise<{
        matches: number;
    }>;
    getAiResultById(id: string): Promise<AiResult>;
    createAiResult(payload: AiResultPostPayload): Promise<AiResult>;
    updateAiResult(id: string, payload: Partial<AiResultPostPayload>): Promise<AiResult>;
    deleteAiResult(id: string): Promise<void>;
}
export {};
