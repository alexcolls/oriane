import { ProfileCollectorService } from './profile-collector.service';
import { CollectProfileQueryDto } from './dto/profile-collector.dto';
export declare class ProfileCollectorController {
    private readonly profileCollectorService;
    private readonly logger;
    constructor(profileCollectorService: ProfileCollectorService);
    collectUserProfile(queryDto: CollectProfileQueryDto): Promise<{
        success: boolean;
        message: string;
    }>;
}
