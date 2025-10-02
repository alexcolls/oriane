import { OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
export declare class AwsSqsService implements OnModuleInit {
    private configService;
    private sqsClient;
    private queueUrl;
    private readonly logger;
    constructor(configService: ConfigService, queueUrl: string);
    onModuleInit(): Promise<void>;
    sendMessage(messageBody: any): Promise<void>;
    receiveMessages(maxNumberOfMessages?: number): Promise<any[]>;
    deleteMessage(receiptHandle: string): Promise<void>;
    sendMessageBatch(messages: any[], batchSize?: number): Promise<{
        success: number;
        errors: number;
        failedMessages: any[];
    }>;
}
