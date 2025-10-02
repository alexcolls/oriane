export declare function retry<T>(fn: () => Promise<T>, maxRetries?: number): Promise<T>;
export declare function cleanURL(url: string): string;
export declare function sleep(ms: number): Promise<void>;
export declare function downloadBufferFromUrl(url: string): Promise<Buffer>;
