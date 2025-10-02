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
var AwsSqsService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AwsSqsService = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const client_sqs_1 = require("@aws-sdk/client-sqs");
const MAX_SOCKETS = 300;
const SOCKETS_TIMEOUT = 30000;
let AwsSqsService = AwsSqsService_1 = class AwsSqsService {
    constructor(configService, queueUrl) {
        this.configService = configService;
        this.logger = new common_1.Logger(AwsSqsService_1.name);
        this.queueUrl = queueUrl;
    }
    async onModuleInit() {
        const region = this.configService.get('AWS_REGION');
        const accessKeyId = this.configService.get('AWS_ACCESS_KEY_ID');
        const secretAccessKey = this.configService.get('AWS_SECRET_ACCESS_KEY');
        if (!region || !accessKeyId || !secretAccessKey) {
            throw new Error('Missing required AWS configuration. Please check your environment variables.');
        }
        this.sqsClient = new client_sqs_1.SQSClient({
            region,
            credentials: {
                accessKeyId,
                secretAccessKey,
            },
            requestHandler: {
                httpsAgent: { maxSockets: MAX_SOCKETS },
                socketAcquisitionTimeout: SOCKETS_TIMEOUT,
            },
        });
        this.logger.log('AWS SQS client initialized successfully');
        this.logger.log(`SQS Queue URL: ${this.queueUrl}`);
        this.logger.log(`AWS Region: ${region}`);
    }
    async sendMessage(messageBody) {
        this.logger.log(`Attempting to send message to SQS queue: ${this.queueUrl}`);
        this.logger.log(`Message body: ${JSON.stringify(messageBody, null, 2)}`);
        const command = new client_sqs_1.SendMessageCommand({
            QueueUrl: this.queueUrl,
            MessageBody: JSON.stringify(messageBody),
        });
        try {
            const result = await this.sqsClient.send(command);
            this.logger.log(`Successfully sent message to SQS. MessageId: ${result.MessageId}`);
        }
        catch (error) {
            this.logger.error('Error sending message to SQS:', error);
            console.error('Error sending message to SQS:', error);
            console.error('SQS Queue URL:', this.queueUrl);
            console.error('Error details:', JSON.stringify(error, null, 2));
            throw error;
        }
    }
    async receiveMessages(maxNumberOfMessages = 10) {
        const command = new client_sqs_1.ReceiveMessageCommand({
            QueueUrl: this.queueUrl,
            MaxNumberOfMessages: maxNumberOfMessages,
        });
        try {
            const response = await this.sqsClient.send(command);
            return response.Messages || [];
        }
        catch (error) {
            console.error('Error receiving messages from SQS:', error);
            throw error;
        }
    }
    async deleteMessage(receiptHandle) {
        const command = new client_sqs_1.DeleteMessageCommand({
            QueueUrl: this.queueUrl,
            ReceiptHandle: receiptHandle,
        });
        try {
            await this.sqsClient.send(command);
        }
        catch (error) {
            console.error('Error deleting message from SQS:', error);
            throw error;
        }
    }
    async sendMessageBatch(messages, batchSize = 10) {
        if (messages.length === 0) {
            return { success: 0, errors: 0, failedMessages: [] };
        }
        const maxBatchSize = Math.min(batchSize, 10);
        const batches = [];
        for (let i = 0; i < messages.length; i += maxBatchSize) {
            batches.push(messages.slice(i, i + maxBatchSize));
        }
        let totalSuccess = 0;
        let totalErrors = 0;
        const failedMessages = [];
        this.logger.log(`Sending ${messages.length} messages in ${batches.length} batches`);
        for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
            const batch = batches[batchIndex];
            try {
                const entries = batch.map((message, index) => ({
                    Id: `${batchIndex}-${index}`,
                    MessageBody: JSON.stringify(message),
                }));
                const command = new client_sqs_1.SendMessageBatchCommand({
                    QueueUrl: this.queueUrl,
                    Entries: entries,
                });
                const response = await this.sqsClient.send(command);
                const successful = response.Successful?.length || 0;
                const failed = response.Failed?.length || 0;
                totalSuccess += successful;
                totalErrors += failed;
                if (failed > 0 && response.Failed) {
                    this.logger.warn(`Batch ${batchIndex} had ${failed} failed messages:`, response.Failed);
                    response.Failed.forEach((failedEntry) => {
                        const originalIndex = parseInt(failedEntry.Id?.split('-')[1] || '0');
                        failedMessages.push(batch[originalIndex]);
                    });
                }
                this.logger.debug(`Batch ${batchIndex + 1}/${batches.length}: ${successful} sent, ${failed} failed`);
            }
            catch (error) {
                this.logger.error(`Error sending batch ${batchIndex}:`, error);
                totalErrors += batch.length;
                failedMessages.push(...batch);
            }
        }
        this.logger.log(`Batch send completed: ${totalSuccess} successful, ${totalErrors} failed`);
        return {
            success: totalSuccess,
            errors: totalErrors,
            failedMessages,
        };
    }
};
exports.AwsSqsService = AwsSqsService;
exports.AwsSqsService = AwsSqsService = AwsSqsService_1 = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [config_1.ConfigService, String])
], AwsSqsService);
//# sourceMappingURL=aws.sqs.service.js.map