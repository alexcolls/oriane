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
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AuthController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const auth_service_1 = require("./auth.service");
const login_dto_1 = require("./dto/login.dto");
const forgot_password_dto_1 = require("./dto/forgot-password.dto");
const confirm_forgot_password_dto_1 = require("./dto/confirm-forgot-password.dto");
const public_decorator_1 = require("../decorators/public.decorator");
let AuthController = class AuthController {
    constructor(authService) {
        this.authService = authService;
    }
    async login(body) {
        if (!body.email || !body.password) {
            throw new common_1.BadRequestException('Email and password are required');
        }
        return this.authService.login(body.email, body.password);
    }
    async logout(req) {
        const accessToken = req.headers.authorization.split(' ')[1];
        await this.authService.logout(accessToken);
        return { message: 'Logout successful' };
    }
    async recoverPassword(body) {
        if (!body.email) {
            throw new common_1.BadRequestException('Email is required');
        }
        return this.authService.recoverPassword(body.email);
    }
    async confirmRecoverPassword(body) {
        if (!body.email || !body.code || !body.newPassword) {
            throw new common_1.BadRequestException('Email, code, and newPassword are required');
        }
        return this.authService.confirmRecoverPassword(body.email, body.code, body.newPassword);
    }
};
exports.AuthController = AuthController;
__decorate([
    (0, public_decorator_1.Public)(),
    (0, common_1.Post)('login'),
    (0, swagger_1.ApiOperation)({ summary: 'User login' }),
    (0, swagger_1.ApiBody)({ type: login_dto_1.LoginDto }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Login successful, returns tokens.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 400,
        description: 'Invalid input (e.g., missing fields).',
    }),
    (0, swagger_1.ApiResponse)({
        status: 401,
        description: 'Unauthorized (e.g., invalid credentials).',
    }),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [login_dto_1.LoginDto]),
    __metadata("design:returntype", Promise)
], AuthController.prototype, "login", null);
__decorate([
    (0, common_1.Post)('logout'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, swagger_1.ApiOperation)({ summary: 'User logout (requires authentication)' }),
    (0, swagger_1.ApiResponse)({ status: common_1.HttpStatus.OK, description: 'Logout successful.' }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.UNAUTHORIZED,
        description: 'Unauthorized (no token or invalid token).',
    }),
    (0, swagger_1.ApiResponse)({
        status: common_1.HttpStatus.BAD_REQUEST,
        description: 'Missing or malformed authorization header.',
    }),
    __param(0, (0, common_1.Req)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object]),
    __metadata("design:returntype", Promise)
], AuthController.prototype, "logout", null);
__decorate([
    (0, public_decorator_1.Public)(),
    (0, common_1.Post)('recover'),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [forgot_password_dto_1.ForgotPasswordDto]),
    __metadata("design:returntype", Promise)
], AuthController.prototype, "recoverPassword", null);
__decorate([
    (0, public_decorator_1.Public)(),
    (0, common_1.Post)('confirm-recover'),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [confirm_forgot_password_dto_1.ConfirmForgotPasswordDto]),
    __metadata("design:returntype", Promise)
], AuthController.prototype, "confirmRecoverPassword", null);
exports.AuthController = AuthController = __decorate([
    (0, swagger_1.ApiTags)('Authentication'),
    (0, common_1.Controller)('auth'),
    __metadata("design:paramtypes", [auth_service_1.AuthService])
], AuthController);
//# sourceMappingURL=auth.controller.js.map