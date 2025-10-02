import { AiError } from '../../../../entities/ai-errors.entity';
export declare class CreateAiErrorDto {
    jobId: string;
    watchedVideo: string;
    error_message: string;
    jobRunId?: string;
}
declare const UpdateAiErrorDto_base: import("@nestjs/common").Type<Partial<CreateAiErrorDto>>;
export declare class UpdateAiErrorDto extends UpdateAiErrorDto_base {
}
export declare class GetAiErrorsQueryDto {
    offset?: number;
    limit?: number;
    search?: string;
}
export declare class GetAiErrorsResponseDto {
    data: AiError[];
    total: number;
}
export {};
