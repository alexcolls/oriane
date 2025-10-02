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
var AwsOsService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AwsOsService = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const opensearch_1 = require("@opensearch-project/opensearch");
const aws_1 = require("@opensearch-project/opensearch/aws");
const credential_provider_node_1 = require("@aws-sdk/credential-provider-node");
const client_sts_1 = require("@aws-sdk/client-sts");
let AwsOsService = AwsOsService_1 = class AwsOsService {
    constructor(config) {
        this.config = config;
        this.logger = new common_1.Logger(AwsOsService_1.name);
        this.videoIndex = this.config.get('OS_VIDEO_INDEX') || 'videos';
        this.frameIndex = this.config.get('OS_FRAME_INDEX') || 'video_frames';
    }
    async onModuleInit() {
        const endpoint = this.config.get('AWS_OPENSEARCH_URL');
        const region = this.config.get('AWS_REGION') || 'us-east-1';
        if (!endpoint)
            throw new Error('Missing AWS_OPENSEARCH_URL');
        const sts = new client_sts_1.STSClient({ region });
        const command = new client_sts_1.GetCallerIdentityCommand({});
        const id = await sts.send(command);
        this.logger.log(`🔑 Calls signed as: ${JSON.stringify(id)}`);
        const signerOptions = {
            region,
            service: 'aoss',
            getCredentials: (0, credential_provider_node_1.defaultProvider)(),
        };
        this.client = new opensearch_1.Client({
            ...(0, aws_1.AwsSigv4Signer)(signerOptions),
            node: endpoint,
        });
        this.logger.log('OpenSearch client initialized');
    }
    getClient() {
        if (!this.client)
            throw new Error('OpenSearch client not ready');
        return this.client;
    }
    async indexDocument(index, id, doc, refresh = true) {
        await this.client.index({
            index,
            id,
            body: doc,
            refresh: refresh ? 'true' : undefined,
        });
        this.logger.log(`Indexed ${id} → ${index}`);
    }
    async bulkIndex(index, items, refresh = false) {
        if (!items.length)
            return;
        const body = items.flatMap((i) => [
            { index: { _index: index, _id: i.id } },
            i.body,
        ]);
        const resp = await this.client.bulk({
            body,
            refresh: refresh ? 'true' : undefined,
        });
        if (resp.body.errors) {
            this.logger.error('Bulk errors', resp.body);
            throw new Error('Bulk indexing failed');
        }
        this.logger.log(`Bulk indexed ${items.length} docs → ${index}`);
    }
    async count(index) {
        const resp = await this.client.count({ index });
        return resp.body.count;
    }
    async search(index, body) {
        const resp = await this.client.search({ index, body });
        const hits = resp.body.hits.hits;
        return hits.map((h) => h._source);
    }
    async deleteById(index, id, refresh = false) {
        await this.client.delete({
            index,
            id,
            refresh: refresh ? 'true' : undefined,
        });
        this.logger.log(`Deleted ${id} from ${index}`);
    }
    async searchSimilarFrames(vector, k = 10, numCandidates = 100, platform) {
        const knnClause = {
            knn: {
                field: 'vector',
                query_vector: vector,
                k,
                num_candidates: numCandidates,
            },
        };
        const body = {
            size: k,
            ...knnClause,
            collapse: { field: 'code' },
            _source: ['code'],
        };
        if (platform) {
            body.query = {
                bool: {
                    filter: [{ term: { platform } }],
                    must: [{ knn: knnClause.knn }],
                },
            };
            delete body.knn;
        }
        const resp = await this.client.search({
            index: this.frameIndex,
            body,
        });
        return resp.body.hits.hits.map((h) => ({
            code: h._source.code,
            score: h._score,
        }));
    }
    async searchSimilarVideos(vector, k = 10, numCandidates = 100, platform) {
        const knn = {
            field: 'vector',
            query_vector: vector,
            k,
            num_candidates: numCandidates,
        };
        if (platform) {
            knn.filter = { term: { platform } };
        }
        const body = {
            size: k,
            knn,
            _source: ['code'],
        };
        const resp = await this.client.search({
            index: this.videoIndex,
            body,
        });
        return resp.body.hits.hits.map((h) => ({
            code: h._source.code,
            score: h._score,
        }));
    }
};
exports.AwsOsService = AwsOsService;
exports.AwsOsService = AwsOsService = AwsOsService_1 = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [config_1.ConfigService])
], AwsOsService);
//# sourceMappingURL=aws.os.service.js.map