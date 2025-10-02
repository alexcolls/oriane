import { AwsCognitoService } from '../aws/aws.cognito.service';
export declare class AuthService {
    private readonly awsCognitoService;
    constructor(awsCognitoService: AwsCognitoService);
    login(email: string, password: string): Promise<any>;
    register(email: string, password: string): Promise<any>;
    recoverPassword(email: string): Promise<any>;
    confirmRecoverPassword(email: string, code: string, newPassword: string): Promise<any>;
    confirmRegistration(email: string, code: string): Promise<any>;
    logout(email: string): Promise<any>;
}
