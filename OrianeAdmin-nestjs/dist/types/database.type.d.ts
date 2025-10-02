export interface OrianeUser {
    id: string;
    next_check_at?: Date;
    check_frequency: number;
    priority: 'low' | 'medium' | 'high';
    environment: string;
    last_cursor?: Date;
    last_checked?: Date;
    username: string;
    is_creator: boolean;
    is_deactivated: boolean;
    is_watched: boolean;
    state_error: boolean;
    account_status: string;
    error_message?: string;
    first_fetched?: Date;
    created_at: Date;
}
