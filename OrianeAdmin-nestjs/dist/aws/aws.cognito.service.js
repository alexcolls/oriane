"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AwsCognitoService = void 0;
const common_1 = require("@nestjs/common");
const amazon_cognito_identity_js_1 = require("amazon-cognito-identity-js");
const client_cognito_identity_provider_1 = require("@aws-sdk/client-cognito-identity-provider");
let AwsCognitoService = class AwsCognitoService {
    constructor() {
        this.userPool = new amazon_cognito_identity_js_1.CognitoUserPool({
            UserPoolId: process.env.COGNITO_USER_POOL_ID,
            ClientId: process.env.COGNITO_CLIENT_ID,
        });
        this.cognitoClient = new client_cognito_identity_provider_1.CognitoIdentityProviderClient({
            region: process.env.AWS_REGION || 'us-east-1',
        });
    }
    async registerUser(email, password) {
        const attributeList = [
            new amazon_cognito_identity_js_1.CognitoUserAttribute({
                Name: 'email',
                Value: email,
            }),
        ];
        return new Promise((resolve, reject) => {
            this.userPool.signUp(email, password, attributeList, null, (err, result) => {
                if (err) {
                    return reject(err);
                }
                resolve(result);
            });
        });
    }
    async authenticateUser(email, password) {
        const authenticationDetails = new amazon_cognito_identity_js_1.AuthenticationDetails({
            Username: email,
            Password: password,
        });
        const userData = {
            Username: email,
            Pool: this.userPool,
        };
        const cognitoUser = new amazon_cognito_identity_js_1.CognitoUser(userData);
        return new Promise((resolve, reject) => {
            cognitoUser.authenticateUser(authenticationDetails, {
                onSuccess: (result) => {
                    resolve({
                        accessToken: result.getAccessToken().getJwtToken(),
                        idToken: result.getIdToken().getJwtToken(),
                        refreshToken: result.getRefreshToken().getToken(),
                    });
                },
                onFailure: (err) => {
                    reject(err);
                },
            });
        });
    }
    async logoutUser(accessToken) {
        const command = new client_cognito_identity_provider_1.GlobalSignOutCommand({
            AccessToken: accessToken,
        });
        await this.cognitoClient.send(command);
    }
    async forgotPassword(email) {
        const userData = {
            Username: email,
            Pool: this.userPool,
        };
        const cognitoUser = new amazon_cognito_identity_js_1.CognitoUser(userData);
        return new Promise((resolve, reject) => {
            cognitoUser.forgotPassword({
                onSuccess: (data) => {
                    resolve({ message: 'Password recovery initiated', data });
                },
                onFailure: (err) => {
                    reject(err);
                },
            });
        });
    }
    async refreshToken(refreshToken) {
        const command = new client_cognito_identity_provider_1.InitiateAuthCommand({
            AuthFlow: 'REFRESH_TOKEN_AUTH',
            ClientId: process.env.COGNITO_CLIENT_ID,
            AuthParameters: {
                REFRESH_TOKEN: refreshToken,
            },
        });
        const response = await this.cognitoClient.send(command);
        return {
            accessToken: response.AuthenticationResult.AccessToken,
            idToken: response.AuthenticationResult.IdToken,
            refreshToken: response.AuthenticationResult.RefreshToken || refreshToken,
        };
    }
    async confirmForgotPassword(email, code, newPassword) {
        const userData = {
            Username: email,
            Pool: this.userPool,
        };
        const cognitoUser = new amazon_cognito_identity_js_1.CognitoUser(userData);
        return new Promise((resolve, reject) => {
            cognitoUser.confirmPassword(code, newPassword, {
                onSuccess: () => {
                    resolve({ message: 'Password reset successful' });
                },
                onFailure: (err) => {
                    reject(err);
                },
            });
        });
    }
    async confirmRegistration(email, code) {
        const userData = {
            Username: email,
            Pool: this.userPool,
        };
        const cognitoUser = new amazon_cognito_identity_js_1.CognitoUser(userData);
        return new Promise((resolve, reject) => {
            cognitoUser.confirmRegistration(code, true, (err, result) => {
                if (err) {
                    return reject(err);
                }
                resolve({ message: 'Email confirmed successfully', result });
            });
        });
    }
};
exports.AwsCognitoService = AwsCognitoService;
exports.AwsCognitoService = AwsCognitoService = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [])
], AwsCognitoService);
//# sourceMappingURL=aws.cognito.service.js.map