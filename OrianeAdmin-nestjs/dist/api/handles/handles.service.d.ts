import { Repository } from 'typeorm';
import { OrianeUser } from '../../entities/oriane-user.entity';
import { InstaProfile } from '../../entities/insta-profiles.entity';
import { InstaContent } from '../../entities/content.entity';
import { type ApiFilter } from '../../utils/api';
import { AwsSqsService } from '../../aws/aws.sqs.service';
export declare class HandlesService {
    private readonly orianeUserRepository;
    private readonly instaProfileRepository;
    private readonly instaContentRepository;
    private readonly sqsHandlesService;
    private readonly logger;
    constructor(orianeUserRepository: Repository<OrianeUser>, instaProfileRepository: Repository<InstaProfile>, instaContentRepository: Repository<InstaContent>, sqsHandlesService: AwsSqsService);
    private getNextMonthStart;
    uploadCSV(file: Express.Multer.File): Promise<{
        success: boolean;
        message: string;
    }>;
    processUsernamesViaSqs(usernames: string[]): Promise<void>;
    testSqsConnection(): Promise<void>;
    private addWatchedHandleInternal;
    addUser(username: string, priority: string, environment?: string): Promise<{
        message: string;
        data: OrianeUser;
    }>;
    addWatchedHandle(username: string): Promise<{
        message: string;
        data?: any;
    }>;
    updateHandle(currentUsername: string, updates: Partial<Pick<OrianeUser, 'username' | 'priority' | 'isCreator' | 'isWatched'>>): Promise<{
        message: string;
        updatedUser: OrianeUser;
    }>;
    deactivateHandle(username: string): Promise<OrianeUser>;
    activateHandle(username: string): Promise<OrianeUser>;
    getHandleByUsername(username: string): Promise<OrianeUser>;
    getHandles(environment: string, user_type: 'users' | 'watched', offset: number, limit: number, search?: string, filters?: ApiFilter[]): Promise<{
        data: OrianeUser[];
        total: number;
    }>;
    getVideoCodesByUsername(user_type: 'users' | 'watched', offset: number, limit: number, search?: string): Promise<{
        data: {
            username: string;
            video_codes: string[];
        }[];
        total: number;
    }>;
    getAllVideoCodes(user_type: 'users' | 'watched'): Promise<string[]>;
}
