import { HandleSchedulerService } from './handle-scheduler.service';
import { RunUserScrapingDto } from './dto/handle-scheduler.dto';
export declare class HandleSchedulerController {
    private readonly handleSchedulerService;
    private readonly logger;
    constructor(handleSchedulerService: HandleSchedulerService);
    runUserScraping(dto: RunUserScrapingDto): Promise<{
        success: boolean;
        message: string;
    }>;
    runScheduleHandles(): Promise<{
        success: boolean;
        message: string;
    }>;
    reRunScheduleHandles(): Promise<{
        success: boolean;
        message: string;
    }>;
    refreshAllHandles(): Promise<{
        success: boolean;
        message: string;
    }>;
    refreshAllHandlesProgress(): Promise<{
        total: number;
        checked_today: number;
        progress: number;
    }>;
}
