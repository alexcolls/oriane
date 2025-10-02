import { InstaProfilesService } from './insta-profiles.service';
import { CreateInstaProfileDto, UpdateInstaProfileDto, GetInstaProfilesQueryDto, InstaProfileResponseDto } from './dto/insta-profile.dto';
export declare class InstaProfilesController {
    private readonly profilesService;
    private readonly logger;
    constructor(profilesService: InstaProfilesService);
    getAllProfiles(queryDto: GetInstaProfilesQueryDto): Promise<InstaProfileResponseDto[]>;
    getProfileByUsername(username: string): Promise<InstaProfileResponseDto>;
    getProfileById(id: string): Promise<InstaProfileResponseDto>;
    createProfile(createProfileDto: CreateInstaProfileDto): Promise<InstaProfileResponseDto>;
    updateProfile(id: string, updateData: UpdateInstaProfileDto): Promise<InstaProfileResponseDto>;
    deleteProfile(id: string): Promise<void>;
}
