import { UserPriority } from '../../../entities/oriane-user.entity';
export declare class AddUserDto {
    username: string;
    priority: UserPriority;
    environment?: string;
}
export declare class AddWatchedHandleDto {
    username: string;
}
export declare class UpdateHandlePayloadDto {
    username?: string;
    priority?: UserPriority;
    isCreator?: boolean;
    isWatched?: boolean;
}
export declare class UpdateHandleDto {
    currentUsername: string;
}
export declare class DeactivateHandleDto {
    username: string;
}
export declare class ActivateHandleDto {
    username: string;
}
export declare class GetHandlesQueryDto {
    environment?: string;
    user_type?: 'users' | 'watched';
    offset?: number;
    limit?: number;
    search?: string;
    filters?: string;
}
export declare class GetVideoCodesQueryDto {
    user_type: 'users' | 'watched';
    offset?: number;
    limit?: number;
    search?: string;
}
export declare class GetAllVideoCodesQueryDto {
    user_type: 'users' | 'watched';
}
