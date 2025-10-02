import { OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Client as OpenSearchClient } from '@opensearch-project/opensearch';
export declare class AwsOsService implements OnModuleInit {
    private readonly config;
    private client;
    private readonly logger;
    private readonly videoIndex;
    private readonly frameIndex;
    constructor(config: ConfigService);
    onModuleInit(): Promise<void>;
    getClient(): OpenSearchClient;
    indexDocument<T = any>(index: string, id: string, doc: T, refresh?: boolean): Promise<void>;
    bulkIndex<T = any>(index: string, items: Array<{
        id: string;
        body: T;
    }>, refresh?: boolean): Promise<void>;
    count(index: string): Promise<number>;
    search<T = any>(index: string, body: Record<string, any>): Promise<T[]>;
    deleteById(index: string, id: string, refresh?: boolean): Promise<void>;
    searchSimilarFrames(vector: number[], k?: number, numCandidates?: number, platform?: string): Promise<Array<{
        code: string;
        score: number;
    }>>;
    searchSimilarVideos(vector: number[], k?: number, numCandidates?: number, platform?: string): Promise<Array<{
        code: string;
        score: number;
    }>>;
}
