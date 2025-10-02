export declare class AwsCognitoService {
    private userPool;
    private cognitoClient;
    constructor();
    registerUser(email: string, password: string): Promise<any>;
    authenticateUser(email: string, password: string): Promise<any>;
    logoutUser(accessToken: string): Promise<void>;
    forgotPassword(email: string): Promise<any>;
    refreshToken(refreshToken: string): Promise<any>;
    confirmForgotPassword(email: string, code: string, newPassword: string): Promise<any>;
    confirmRegistration(email: string, code: string): Promise<any>;
}
