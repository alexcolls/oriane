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
var OpenSearchService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.OpenSearchService = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const axios_1 = require("axios");
const credential_provider_node_1 = require("@aws-sdk/credential-provider-node");
const client_bedrock_runtime_1 = require("@aws-sdk/client-bedrock-runtime");
const aws_os_service_1 = require("../../aws/aws.os.service");
let OpenSearchService = OpenSearchService_1 = class OpenSearchService {
    constructor(configService, awsOsService) {
        this.configService = configService;
        this.awsOsService = awsOsService;
        this.logger = new common_1.Logger(OpenSearchService_1.name);
        this.region = this.configService.get('AWS_REGION') || 'us-east-1';
        this.imageModelId =
            this.configService.get('IMAGE_MODEL_ID') ||
                'amazon.titan-embed-image-v1';
        this.textModelId =
            this.configService.get('TEXT_MODEL_ID') ||
                'amazon.titan-embed-text-v2:0';
        this.embDim = Number(this.configService.get('EMB_DIM') || '1024');
        this.bedrockClient = new client_bedrock_runtime_1.BedrockRuntimeClient({
            region: this.region,
            credentials: (0, credential_provider_node_1.defaultProvider)(),
        });
        this.logger.log('OpenSearchService instantiated and BedrockRuntimeClient initialized.');
    }
    async invokeBedrockModel(modelId, body) {
        const commandInput = {
            modelId,
            contentType: 'application/json',
            accept: 'application/json',
            body: JSON.stringify(body),
        };
        try {
            const command = new client_bedrock_runtime_1.InvokeModelCommand(commandInput);
            const rawResponse = await this.bedrockClient.send(command);
            const bodyText = new TextDecoder().decode(rawResponse.body);
            const parsedResponse = JSON.parse(bodyText);
            if (!parsedResponse.embedding ||
                !Array.isArray(parsedResponse.embedding)) {
                this.logger.error('Bedrock InvokeModel response missing or invalid embedding array:', parsedResponse);
                throw new common_1.InternalServerErrorException('Failed to get valid embedding from Bedrock model.');
            }
            return parsedResponse.embedding;
        }
        catch (error) {
            this.logger.error(`Error invoking Bedrock model ${modelId}: ${error.message}`, error.stack);
            if (error instanceof common_1.HttpException)
                throw error;
            throw new common_1.InternalServerErrorException(`Bedrock model invocation failed for ${modelId}: ${error.message}`);
        }
    }
    async searchVideosByImage(imageUrl, k = 10, numCandidates = 100, platform) {
        this.logger.debug(`Searching videos by image URL: ${imageUrl}`);
        let imgB64;
        try {
            const response = await axios_1.default.get(imageUrl, {
                responseType: 'arraybuffer',
            });
            imgB64 = Buffer.from(response.data).toString('base64');
        }
        catch (error) {
            this.logger.error(`Failed to fetch or encode image from URL ${imageUrl}: ${error.message}`, error.stack);
            throw new common_1.HttpException('Failed to fetch image from URL.', common_1.HttpStatus.BAD_REQUEST);
        }
        const embedding = await this.invokeBedrockModel(this.imageModelId, {
            inputImage: imgB64,
            embeddingConfig: { outputEmbeddingLength: this.embDim },
        });
        this.logger.debug(`Performing k-NN search with ${embedding.length}-dim vector, k=${k}, numCandidates=${numCandidates}`);
        return this.awsOsService.searchSimilarFrames(embedding, k, numCandidates, platform);
    }
    async embedImageFromBase64(b64) {
        this.logger.debug('Embedding image from Base64 string.');
        return this.invokeBedrockModel(this.imageModelId, {
            inputImage: b64,
            embeddingConfig: { outputEmbeddingLength: this.embDim },
        });
    }
    async embedImageFromUrl(url) {
        this.logger.debug(`Embedding image from URL: ${url}`);
        let imgB64;
        try {
            const response = await axios_1.default.get(url, {
                responseType: 'arraybuffer',
            });
            imgB64 = Buffer.from(response.data).toString('base64');
        }
        catch (error) {
            this.logger.error(`Failed to fetch image for embedding from URL ${url}: ${error.message}`, error.stack);
            throw new common_1.HttpException('Failed to fetch image from URL for embedding.', common_1.HttpStatus.BAD_REQUEST);
        }
        return this.embedImageFromBase64(imgB64);
    }
    async embedImageFromBuffer(buf) {
        this.logger.debug('Embedding image from buffer.');
        const b64 = Buffer.isBuffer(buf)
            ? buf.toString('base64')
            : Buffer.from(buf).toString('base64');
        return this.embedImageFromBase64(b64);
    }
    async searchSimilarVideosFromBase64(b64, k = 10, numCandidates = 100, platform) {
        this.logger.debug('Searching similar videos from Base64 image string.');
        const vector = await this.embedImageFromBase64(b64);
        return this.awsOsService.searchSimilarVideos(vector, k, numCandidates, platform);
    }
    async embedText(text) {
        this.logger.debug(`Embedding text (first 50 chars): "${text.substring(0, 50)}..."`);
        return this.invokeBedrockModel(this.textModelId, {
            inputText: text,
            ...(this.textModelId.includes('-v2') && {
                dimensions: this.embDim,
                normalize: true,
            }),
        });
    }
    async searchVideosHybrid(queryText, size = 10, _numCandidates = 100) {
        this.logger.debug(`Performing hybrid search for query: "${queryText}"`);
        const queryVector = await this.embedText(queryText);
        const textSearchQueryBody = {
            size,
            query: {
                multi_match: {
                    query: queryText,
                    fields: ['code.text^3', 'platform.text', 'video_id'],
                },
            },
            _source: ['code'],
        };
        this.logger.debug('Performing text-only part of hybrid search...');
        const textHits = await this.awsOsService.search('videos', textSearchQueryBody);
        const vectorSearchQueryBody = {
            size,
            _source: ['code'],
            query: {
                knn: {
                    [this.configService.get('OPENSEARCH_VECTOR_FIELD_NAME') ||
                        'vector']: {
                        vector: queryVector,
                        k: size,
                    },
                },
            },
        };
        this.logger.debug('Performing vector (k-NN) part of hybrid search...');
        const vecHits = await this.awsOsService.search('videos', vectorSearchQueryBody);
        const alpha = 0.5;
        const scores = new Map();
        this.logger.debug(`Text hits: ${textHits.length}, Vector hits: ${vecHits.length} before re-ranking.`);
        textHits.forEach((hit, i) => {
            scores.set(hit.code, (scores.get(hit.code) || 0) + alpha * (1 / (i + 1)));
        });
        vecHits.forEach((hit, i) => {
            scores.set(hit.code, (scores.get(hit.code) || 0) + (1 - alpha) * (1 / (i + 1)));
        });
        const rerankedResults = Array.from(scores.entries())
            .sort(([, scoreA], [, scoreB]) => scoreB - scoreA)
            .slice(0, size)
            .map(([code, score]) => ({ code, score }));
        this.logger.debug(`Hybrid search re-ranked results count: ${rerankedResults.length}`);
        return rerankedResults;
    }
    async embedMultiModal(text, b64Image) {
        this.logger.debug(`Embedding multi-modally (text and image). Text starts: "${text.substring(0, 30)}"`);
        return this.invokeBedrockModel(this.imageModelId, {
            inputText: text,
            inputImage: b64Image,
            embeddingConfig: { outputEmbeddingLength: this.embDim },
        });
    }
};
exports.OpenSearchService = OpenSearchService;
exports.OpenSearchService = OpenSearchService = OpenSearchService_1 = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [config_1.ConfigService,
        aws_os_service_1.AwsOsService])
], OpenSearchService);
//# sourceMappingURL=opensearch.service.js.map