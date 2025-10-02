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
var HandleSchedulerController_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.HandleSchedulerController = void 0;
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const handle_scheduler_service_1 = require("./handle-scheduler.service");
const handle_scheduler_dto_1 = require("./dto/handle-scheduler.dto");
let HandleSchedulerController = HandleSchedulerController_1 = class HandleSchedulerController {
    constructor(handleSchedulerService) {
        this.handleSchedulerService = handleSchedulerService;
        this.logger = new common_1.Logger(HandleSchedulerController_1.name);
    }
    async runUserScraping(dto) {
        this.logger.log(`Request to process single user: ${dto.username}`);
        return await this.handleSchedulerService.processSingleUser(dto.username);
    }
    async runScheduleHandles() {
        this.logger.log('Request to manually trigger scheduleHandles processing.');
        try {
            await this.handleSchedulerService.scheduleHandles();
            return {
                success: true,
                message: 'Scheduled handles processing triggered successfully.',
            };
        }
        catch (error) {
            this.logger.error(`Error triggering scheduleHandles: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException(error.message || 'Failed to trigger scheduled handles processing.');
        }
    }
    async reRunScheduleHandles() {
        this.logger.log('Request to manually trigger reRunSchedule processing.');
        try {
            await this.handleSchedulerService.reRunSchedule();
            return {
                success: true,
                message: 'Re-run schedule for pending users triggered successfully.',
            };
        }
        catch (error) {
            this.logger.error(`Error triggering reRunSchedule: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException(error.message || 'Failed to trigger re-run schedule.');
        }
    }
    async refreshAllHandles() {
        this.logger.log('Request to manually trigger refreshAllHandles.');
        try {
            await this.handleSchedulerService.refreshAllHandles();
            return {
                success: true,
                message: 'All handles refresh process triggered successfully.',
            };
        }
        catch (error) {
            this.logger.error(`Error triggering refreshAllHandles: ${error.message}`, error.stack);
            throw new common_1.InternalServerErrorException(error.message || 'Failed to trigger refresh all handles.');
        }
    }
    async refreshAllHandlesProgress() {
        this.logger.log('Request to get refreshAllHandles progress.');
        try {
            return await this.handleSchedulerService.refreshAllHandlesProgress();
        }
        catch (error) {
            this.logger.error(`Error fetching refreshAllHandlesProgress: ${error.message}`, error.stack);
            throw new common_1.HttpException(error.message || 'Failed to get refresh handles progress', error.status || common_1.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
};
exports.HandleSchedulerController = HandleSchedulerController;
__decorate([
    (0, common_1.Post)('run-user'),
    (0, swagger_1.ApiOperation)({ summary: 'Process a single user by their username.' }),
    (0, swagger_1.ApiBody)({ type: handle_scheduler_dto_1.RunUserScrapingDto }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'User processing initiated and result returned.',
    }),
    (0, swagger_1.ApiResponse)({ status: 404, description: 'User not found by the service.' }),
    (0, swagger_1.ApiResponse)({
        status: 500,
        description: 'Internal server error during processing.',
    }),
    __param(0, (0, common_1.Body)(common_1.ValidationPipe)),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [handle_scheduler_dto_1.RunUserScrapingDto]),
    __metadata("design:returntype", Promise)
], HandleSchedulerController.prototype, "runUserScraping", null);
__decorate([
    (0, common_1.Post)('trigger-scheduled-handles'),
    (0, swagger_1.ApiOperation)({
        summary: 'Manually trigger the processing of handles due for a check.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Scheduled handles processing triggered successfully.',
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], HandleSchedulerController.prototype, "runScheduleHandles", null);
__decorate([
    (0, common_1.Post)('trigger-rerun-schedule'),
    (0, swagger_1.ApiOperation)({
        summary: 'Manually trigger the re-run schedule for unverified/error users.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Re-run schedule triggered successfully.',
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], HandleSchedulerController.prototype, "reRunScheduleHandles", null);
__decorate([
    (0, common_1.Post)('trigger-refresh-all-handles'),
    (0, swagger_1.ApiOperation)({
        summary: 'Manually trigger a refresh (re-processing) of all non-deactivated handles.',
    }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Refresh all handles process triggered successfully.',
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], HandleSchedulerController.prototype, "refreshAllHandles", null);
__decorate([
    (0, common_1.Get)('refresh-progress'),
    (0, swagger_1.ApiOperation)({ summary: 'Get the progress of the handle refresh process.' }),
    (0, swagger_1.ApiResponse)({
        status: 200,
        description: 'Current refresh progress statistics.',
    }),
    (0, swagger_1.ApiResponse)({ status: 500, description: 'Internal server error.' }),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], HandleSchedulerController.prototype, "refreshAllHandlesProgress", null);
exports.HandleSchedulerController = HandleSchedulerController = HandleSchedulerController_1 = __decorate([
    (0, swagger_1.ApiTags)('Tasks - Handle Scheduler'),
    (0, swagger_1.ApiBearerAuth)(),
    (0, common_1.Controller)('handle-scheduler'),
    __metadata("design:paramtypes", [handle_scheduler_service_1.HandleSchedulerService])
], HandleSchedulerController);
//# sourceMappingURL=handle-scheduler.controller.js.map