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
exports.AuthService = void 0;
const common_1 = require("@nestjs/common");
const aws_cognito_service_1 = require("../aws/aws.cognito.service");
let AuthService = class AuthService {
    constructor(awsCognitoService) {
        this.awsCognitoService = awsCognitoService;
    }
    async login(email, password) {
        try {
            const result = await this.awsCognitoService.authenticateUser(email, password);
            return {
                success: true,
                statusCode: 200,
                data: result,
            };
        }
        catch (error) {
            return {
                success: false,
                statusCode: 401,
                message: error.message || 'Authentication failed',
            };
        }
    }
    async register(email, password) {
        try {
            await this.awsCognitoService.registerUser(email, password);
            return {
                success: true,
                statusCode: 201,
                message: 'User registered successfully. Please verify your email.',
            };
        }
        catch (error) {
            return {
                success: false,
                statusCode: 400,
                message: error.message || 'Registration failed',
            };
        }
    }
    async recoverPassword(email) {
        try {
            await this.awsCognitoService.forgotPassword(email);
            return {
                success: true,
                statusCode: 200,
                message: 'Password recovery email sent. Please check your inbox.',
            };
        }
        catch (error) {
            return {
                success: false,
                statusCode: 500,
                message: error.message || 'Failed to initiate password recovery',
            };
        }
    }
    async confirmRecoverPassword(email, code, newPassword) {
        try {
            await this.awsCognitoService.confirmForgotPassword(email, code, newPassword);
            return {
                success: true,
                statusCode: 200,
                message: 'Password has been reset successfully.',
            };
        }
        catch (error) {
            return {
                success: false,
                statusCode: 500,
                message: error.message || 'Failed to confirm password recovery',
            };
        }
    }
    async confirmRegistration(email, code) {
        try {
            await this.awsCognitoService.confirmRegistration(email, code);
            return {
                success: true,
                statusCode: 200,
                message: 'Email confirmed successfully.',
            };
        }
        catch (error) {
            return {
                success: false,
                statusCode: 500,
                message: error.message || 'Failed to confirm email',
            };
        }
    }
    async logout(email) {
        try {
            await this.awsCognitoService.logoutUser(email);
            return {
                success: true,
                statusCode: 200,
                message: 'User logged out successfully.',
            };
        }
        catch (error) {
            return {
                success: false,
                statusCode: 500,
                message: error.message || 'Failed to log out user',
            };
        }
    }
};
exports.AuthService = AuthService;
exports.AuthService = AuthService = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [aws_cognito_service_1.AwsCognitoService])
], AuthService);
//# sourceMappingURL=auth.service.js.map