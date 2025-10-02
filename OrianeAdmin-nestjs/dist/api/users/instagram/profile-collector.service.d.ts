import { Repository } from 'typeorm';
import { HikerApiClientService } from '../../../api/hiker-api-client/hiker-api-client.service';
import { InstaProfile } from '../../../entities/insta-profiles.entity';
import { OrianeUser } from '../../../entities/oriane-user.entity';
export declare class ProfileCollectorService {
    private readonly hikerApiClient;
    private readonly instaProfileRepository;
    private readonly orianeUserRepository;
    private readonly logger;
    constructor(hikerApiClient: HikerApiClientService, instaProfileRepository: Repository<InstaProfile>, orianeUserRepository: Repository<OrianeUser>);
    collectProfile(username: string): Promise<boolean>;
}
