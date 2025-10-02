import { InstaContent } from '../../../entities/content.entity';
export declare class GetAllContentDto {
    content_type: 'monitored' | 'watched';
    offset: number;
    limit: number;
    search?: string;
}
export declare class GetAllContentResponseDto {
    data: InstaContent[];
    total: number;
}
