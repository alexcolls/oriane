import { Repository } from 'typeorm';
import { AiWarning } from '../../../entities/ai-warnings.entity';
type AiWarningPostPayload = Omit<AiWarning, 'id' | 'createdAt' | 'aiJob' | 'aiJobsRun'>;
export declare class AiWarningsService {
    private readonly aiWarningRepository;
    private readonly logger;
    constructor(aiWarningRepository: Repository<AiWarning>);
    getAiWarnings(offset: number, limit: number, search?: string): Promise<{
        data: AiWarning[];
        total: number;
    }>;
    getAiWarningById(id: string): Promise<AiWarning>;
    createAiWarning(payload: AiWarningPostPayload): Promise<AiWarning>;
    updateAiWarning(id: string, payload: Partial<AiWarningPostPayload>): Promise<AiWarning>;
    deleteAiWarning(id: string): Promise<void>;
}
export {};
