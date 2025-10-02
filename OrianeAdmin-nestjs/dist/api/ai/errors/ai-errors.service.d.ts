import { Repository } from 'typeorm';
import { AiError } from '../../../entities/ai-errors.entity';
import { CreateAiErrorDto, UpdateAiErrorDto, GetAiErrorsQueryDto, GetAiErrorsResponseDto } from './dto/ai-errors.dto';
export declare class AiErrorsService {
    private readonly aiErrorRepository;
    private readonly logger;
    constructor(aiErrorRepository: Repository<AiError>);
    getAiErrors(queryDto: GetAiErrorsQueryDto): Promise<GetAiErrorsResponseDto>;
    getAiErrorById(id: string): Promise<AiError>;
    createAiError(createAiErrorDto: CreateAiErrorDto): Promise<AiError>;
    updateAiError(id: string, updateAiErrorDto: UpdateAiErrorDto): Promise<AiError>;
    deleteAiError(id: string): Promise<void>;
}
