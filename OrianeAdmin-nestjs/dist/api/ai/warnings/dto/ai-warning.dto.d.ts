import { AiWarning } from '../../../../entities/ai-warnings.entity';
export declare class GetAiWarningsQueryDto {
    offset?: number;
    limit?: number;
    search?: string;
}
declare const CreateAiWarningDto_base: import("@nestjs/common").Type<Omit<AiWarning, "id" | "createdAt" | "aiJob" | "aiJobsRun">>;
export declare class CreateAiWarningDto extends CreateAiWarningDto_base {
    jobId: string | null;
    watchedVideo: string | null;
    warningMessage: string | null;
    jobRunId: string | null;
}
declare const UpdateAiWarningDto_base: import("@nestjs/common").Type<Partial<CreateAiWarningDto>>;
export declare class UpdateAiWarningDto extends UpdateAiWarningDto_base {
}
export declare class PaginatedAiWarningsResponseDto {
    data: AiWarning[];
    total: number;
}
export {};
