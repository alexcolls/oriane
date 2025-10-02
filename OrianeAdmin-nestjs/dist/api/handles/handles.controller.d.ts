import { HandlesService } from './handles.service';
import { OrianeUser } from '../../entities/oriane-user.entity';
import { AddUserDto, AddWatchedHandleDto, UpdateHandlePayloadDto, DeactivateHandleDto, ActivateHandleDto, GetHandlesQueryDto, GetVideoCodesQueryDto, GetAllVideoCodesQueryDto } from './dto/handle.dto';
export declare class HandlesController {
    private readonly handlesService;
    private readonly logger;
    constructor(handlesService: HandlesService);
    addUser(addUserDto: AddUserDto): Promise<any>;
    addWatchedHandle(addWatchedDto: AddWatchedHandleDto): Promise<any>;
    uploadCSV(file: Express.Multer.File): Promise<{
        success: boolean;
        message: string;
    }>;
    testSqs(): Promise<{
        success: boolean;
        message: string;
    }>;
    updateHandle(currentUsername: string, updates: UpdateHandlePayloadDto): Promise<any>;
    deactivateHandle(dto: DeactivateHandleDto): Promise<OrianeUser>;
    activateHandle(dto: ActivateHandleDto): Promise<OrianeUser>;
    getHandles(queryDto: GetHandlesQueryDto): Promise<{
        data: OrianeUser[];
        total: number;
    }>;
    getHandleByUsername(username: string): Promise<OrianeUser>;
    getHandlesVideoCodes(queryDto: GetVideoCodesQueryDto): Promise<{
        data: {
            username: string;
            video_codes: string[];
        }[];
        total: number;
    }>;
    getAllVideoCodes(queryDto: GetAllVideoCodesQueryDto): Promise<string[]>;
}
