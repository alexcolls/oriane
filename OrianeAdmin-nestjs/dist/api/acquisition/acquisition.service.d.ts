import { Repository } from 'typeorm';
import { OrianeUser } from '../../entities/oriane-user.entity';
import { GlobalEvent } from '../../entities/global-events.entity';
import { AwsSqsService } from '../../aws/aws.sqs.service';
export declare class AcquisitionService {
    private readonly orianeUserRepository;
    private readonly globalEventRepository;
    private readonly awsSqsAcquisitionService;
    private readonly awsSqsContentService;
    private readonly logger;
    private readonly GLOBAL_EVENT_ID;
    constructor(orianeUserRepository: Repository<OrianeUser>, globalEventRepository: Repository<GlobalEvent>, awsSqsAcquisitionService: AwsSqsService, awsSqsContentService: AwsSqsService);
    runAcquisition(debug?: boolean, batchSize?: number): Promise<{
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
    getAcquisitionProgress(): Promise<{
        total: number;
        fetched: number;
        progress: number;
    }>;
    getLastAcquisitionTimestamp(): Promise<string | null>;
    private updateLastAcquisitionTimestamp;
    private createContentUpdateMessage;
    getMessageFormat(): {
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
    };
    runVideoContentUpdate(videoCode: string): Promise<{
        success: boolean;
        message: string;
    }>;
    runAcquisitionFast(debug?: boolean, batchSize?: number): Promise<{
        total: number;
        dispatched: number;
        errors: number;
        success: boolean;
        message: string;
    }>;
}
