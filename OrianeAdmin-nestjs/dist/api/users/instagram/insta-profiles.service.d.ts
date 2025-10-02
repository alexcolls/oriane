import { Repository } from 'typeorm';
import { InstaProfile } from '../../../entities/insta-profiles.entity';
type InstaProfileCreationPayload = Partial<Omit<InstaProfile, 'id' | 'createdAt' | 'updatedAt' | 'orianeUser' | 'contents'>>;
type InstaProfileUpdatePayload = Partial<Omit<InstaProfile, 'id' | 'createdAt' | 'updatedAt' | 'orianeUser' | 'contents' | 'username'>>;
export declare class InstaProfilesService {
    private readonly instaProfileRepository;
    private readonly logger;
    constructor(instaProfileRepository: Repository<InstaProfile>);
    getAllProfiles(isCreator?: boolean): Promise<InstaProfile[]>;
    getProfileByUsername(username: string): Promise<InstaProfile>;
    getProfileById(id: string): Promise<InstaProfile>;
    createProfile(profileData: InstaProfileCreationPayload): Promise<InstaProfile>;
    updateProfile(id: string, profileUpdateData: InstaProfileUpdatePayload): Promise<InstaProfile>;
    deleteProfile(id: string): Promise<void>;
}
export {};
