import { Repository } from 'typeorm';
import { OrianeUser } from '../../entities/oriane-user.entity';
import { ProfileCollectorService } from '../users/instagram/profile-collector.service';
export declare class HandleSchedulerService {
    private readonly orianeUserRepository;
    private readonly profileCollectorService;
    private readonly logger;
    constructor(orianeUserRepository: Repository<OrianeUser>, profileCollectorService: ProfileCollectorService);
    private getNextMonthStart;
    reRunSchedule(): Promise<void>;
    scheduleHandles(): Promise<void>;
    handleCron(): void;
    processSingleUser(username: string): Promise<{
        success: boolean;
        message: string;
    }>;
    refreshAllHandles(batchSize?: number, concurrentLimit?: number, delayMs?: number): Promise<void>;
    refreshAllHandlesProgress(): Promise<{
        total: number;
        checked_today: number;
        progress: number;
    }>;
}
