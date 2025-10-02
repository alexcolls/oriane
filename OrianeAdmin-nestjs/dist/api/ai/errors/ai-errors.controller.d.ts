import { AiErrorsService } from './ai-errors.service';
import { CreateAiErrorDto, UpdateAiErrorDto, GetAiErrorsQueryDto, GetAiErrorsResponseDto } from './dto/ai-errors.dto';
import { AiError } from '../../../entities/ai-errors.entity';
export declare class AiErrorsController {
    private readonly aiErrorsService;
    constructor(aiErrorsService: AiErrorsService);
    getAiErrors(queryDto: GetAiErrorsQueryDto): Promise<GetAiErrorsResponseDto>;
    getAiErrorById(id: string): Promise<AiError>;
    createAiError(createAiErrorDto: CreateAiErrorDto): Promise<AiError>;
    updateAiError(id: string, updateAiErrorDto: UpdateAiErrorDto): Promise<AiError>;
    deleteAiError(id: string): Promise<void>;
}
