export declare class SearchVideosHybridQueryDto {
    q: string;
    size?: number;
    num_candidates?: number;
}
export declare class SearchVideosByUrlQueryDto {
    url: string;
    k?: number;
    numCandidates?: number;
    platform?: string;
}
export declare class SearchVideosByBase64BodyDto {
    b64: string;
}
export declare class SearchVideosByBase64QueryDto {
    k?: number;
    numCandidates?: number;
    platform?: string;
}
