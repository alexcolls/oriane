"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.BatchService = void 0;
const client_batch_1 = require("@aws-sdk/client-batch");
const common_1 = require("@nestjs/common");
let BatchService = class BatchService {
    constructor() {
        this.client = new client_batch_1.BatchClient({ region: 'us-east-1' });
    }
    async submitSingleExtractionJob(videoCode) {
        const cmd = new client_batch_1.SubmitJobCommand({
            jobName: `crop-${videoCode}`,
            jobQueue: 'gpu-job-queue',
            jobDefinition: 'crop-video-gpu',
            containerOverrides: {
                environment: [{ name: 'VIDEO_CODE', value: videoCode }],
            },
        });
        const res = await this.client.send(cmd);
        return res.jobId;
    }
    async waitForJobs(jobIds) {
        const describe = new client_batch_1.DescribeJobsCommand({ jobs: jobIds });
        let statusMap = {};
        while (Object.values(statusMap).some((s) => s !== 'SUCCEEDED')) {
            const res = await this.client.send(describe);
            statusMap = Object.fromEntries(res.jobs.map((j) => [j.jobId, j.status]));
            console.log('Current job status:', statusMap);
            await new Promise((r) => setTimeout(r, 5000));
        }
    }
};
exports.BatchService = BatchService;
exports.BatchService = BatchService = __decorate([
    (0, common_1.Injectable)()
], BatchService);
//# sourceMappingURL=aws.batch.service.js.map