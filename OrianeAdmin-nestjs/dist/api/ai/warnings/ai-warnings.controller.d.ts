import { AiWarningsService } from './ai-warnings.service';
import { AiWarning } from '../../../entities/ai-warnings.entity';
import { GetAiWarningsQueryDto, CreateAiWarningDto, UpdateAiWarningDto, PaginatedAiWarningsResponseDto } from './dto/ai-warning.dto';
export declare class AiWarningsController {
    private readonly aiWarningsService;
    constructor(aiWarningsService: AiWarningsService);
    getAiWarnings(queryDto: GetAiWarningsQueryDto): Promise<PaginatedAiWarningsResponseDto>;
    getAiWarningById(id: string): Promise<AiWarning>;
    createAiWarning(createDto: CreateAiWarningDto): Promise<AiWarning>;
    updateAiWarning(id: string, updateDto: UpdateAiWarningDto): Promise<AiWarning>;
    deleteAiWarning(id: string): Promise<void>;
}
