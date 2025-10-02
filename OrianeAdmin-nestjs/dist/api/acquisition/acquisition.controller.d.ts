import { AcquisitionService } from './acquisition.service';
export declare class AcquisitionController {
    private readonly acquisitionService;
    private readonly logger;
    constructor(acquisitionService: AcquisitionService);
    runAcquisition(batchSize?: number): Promise<{
        total: number;
        dispatched: number;
        errors: number;
        success: boolean;
        message: string;
    }>;
    runAcquisitionDebug(batchSize?: number): Promise<{
        total: number;
        dispatched: number;
        errors: number;
        success: boolean;
        message: string;
    }>;
    runAcquisitionByUsername(username: string): Promise<{
        success: boolean;
        message: string;
    }>;
    runAcquisitionFast(batchSize?: number): Promise<{
        total: number;
        dispatched: number;
        errors: number;
        success: boolean;
        message: string;
    }>;
    runAcquisitionFastDebug(batchSize?: number): Promise<{
        total: number;
        dispatched: number;
        errors: number;
        success: boolean;
        message: string;
    }>;
    runVideoContentUpdate(videoCode: string): Promise<{
        success: boolean;
        message: string;
    }>;
    getAcquisitionProgress(): Promise<{
        total: number;
        fetched: number;
        progress: number;
    }>;
    getLastAcquisitionTimestamp(): Promise<string>;
    getMessageFormat(): Promise<{
        description: string;
        example: {
            username: string;
            timestamp: string;
            source: string;
            action: string;
        };
        fields: {
            username: string;
            timestamp: string;
            source: string;
            action: string;
        };
    }>;
}
