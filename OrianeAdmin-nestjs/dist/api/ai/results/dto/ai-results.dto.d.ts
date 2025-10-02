import { AiResult } from '../../../../entities/ai-results.entity';
export declare class GetAiResultsQueryDto {
    offset?: number;
    limit?: number;
    order?: 'asc' | 'desc';
    sortBy?: string;
    search?: string;
}
export declare class GetAiMatchesCountQueryDto {
    threshold?: number;
}
declare const CreateAiResultDto_base: import("@nestjs/common").Type<Omit<AiResult, "id" | "createdAt" | "aiJob" | "aiJobsRun">>;
export declare class CreateAiResultDto extends CreateAiResultDto_base {
    jobId: string;
    jobRunId: string;
    model: string;
    monitoredVideo: string;
    watchedVideo: string;
    similarity: number;
    avgSimilarity: number;
    stdSimilarity: number;
    maxSimilarity: number;
    frameResults: FrameResultItemDto[];
    processedInSecs: number;
}
declare const UpdateAiResultDto_base: import("@nestjs/common").Type<Partial<CreateAiResultDto>>;
export declare class UpdateAiResultDto extends UpdateAiResultDto_base {
}
export declare class PaginatedAiResultsResponseDto {
    data: AiResult[];
    total: number;
}
export declare class FrameResultItemDto {
    frame_number: number;
    similarity: number;
}
export {};
