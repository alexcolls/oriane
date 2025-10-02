import { AuthService } from './auth.service';
import { LoginDto } from './dto/login.dto';
import { ForgotPasswordDto } from './dto/forgot-password.dto';
import { ConfirmForgotPasswordDto } from './dto/confirm-forgot-password.dto';
export declare class AuthController {
    private readonly authService;
    constructor(authService: AuthService);
    login(body: LoginDto): Promise<any>;
    logout(req: any): Promise<{
        message: string;
    }>;
    recoverPassword(body: ForgotPasswordDto): Promise<any>;
    confirmRecoverPassword(body: ConfirmForgotPasswordDto): Promise<any>;
}
