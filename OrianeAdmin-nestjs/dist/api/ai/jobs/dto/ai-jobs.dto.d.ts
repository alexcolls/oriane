import { AiJob } from '../../../../entities/ai-jobs.entity';
export declare class QueueAiJobDto {
    monitoredVideo: string;
    model: string;
    useGpu?: boolean;
    threshold?: number;
}
declare const UpdateAiJobDto_base: import("@nestjs/common").Type<Partial<Pick<AiJob, "model" | "useGpu" | "threshold">>>;
export declare class UpdateAiJobDto extends UpdateAiJobDto_base {
}
export declare class GetAiJobsQueryDto {
    offset?: number;
    limit?: number;
    search?: string;
}
declare const AiJobBasicResponseDto_base: import("@nestjs/common").Type<Pick<AiJob, "id" | "createdAt" | "model" | "useGpu" | "monitoredVideo" | "publishedDate" | "threshold">>;
export declare class AiJobBasicResponseDto extends AiJobBasicResponseDto_base {
}
export declare class GetAiJobsResponseDto {
    data: AiJobBasicResponseDto[];
    total: number;
}
export declare class RunJobResultDto {
    jobId: string;
    runId: string;
    totalVideosFound: number;
    videosDispatched: number;
    finalRunState: string;
}
export declare class MonitoredVideoCodeDetailsDto {
    code: string;
    is_extracted: boolean;
}
export declare class MonitoredVideoGroupDto {
    username: string;
    video_codes: MonitoredVideoCodeDetailsDto[];
}
export declare class GetMonitoredVideosResponseDto {
    data: MonitoredVideoGroupDto[];
    total: number;
}
export {};
