import { CallHandler, ExecutionContext, NestInterceptor } from '@nestjs/common';
import { Observable } from 'rxjs';
import { ConfigService } from '@nestjs/config';
export declare class TimeoutInterceptor implements NestInterceptor {
    private readonly configService;
    private readonly logger;
    private readonly defaultTimeout;
    constructor(configService: ConfigService);
    intercept(context: ExecutionContext, next: CallHandler): Observable<any>;
}
