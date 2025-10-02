import { ContentService } from './content.service';
import { GetAllContentDto, GetAllContentResponseDto } from './dto/get-all-content.dto';
import { AddMonitoredContentDto, AddMonitoredContentResponseDto } from './dto/add-monitored-content.dto';
import { RefreshContentResponseDto } from './dto/refresh-content.dto';
export declare class ContentController {
    private readonly contentService;
    private readonly logger;
    constructor(contentService: ContentService);
    getAllContent(query: GetAllContentDto): Promise<GetAllContentResponseDto>;
    getContentCount(): Promise<number>;
    getMonitoredContentCount(): Promise<number>;
    getWatchedContentCount(): Promise<number>;
    getDownloadedVideosCount(): Promise<number>;
    getExtractedVideosCount(): Promise<number>;
    addMonitoredContent(addMonitoredContentDto: AddMonitoredContentDto): Promise<AddMonitoredContentResponseDto>;
    refreshContentByCode(code: string): Promise<RefreshContentResponseDto>;
    getPortraitImage(id_code: string): Promise<Buffer>;
    getImageUrl(id_code: string): Promise<string>;
    getVideo(id_code: string): Promise<Buffer>;
    getVideoUrl(id_code: string): Promise<string>;
    getPublishDateByCode(code: string): Promise<Date | null>;
    getFramesImage(code: string, frame_number: number): Promise<string>;
    deleteContent(code: string): Promise<void>;
    deleteContentById(id: string): Promise<void>;
}
