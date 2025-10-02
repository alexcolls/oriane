import { ExceptionFilter, ArgumentsHost, HttpException } from '@nestjs/common';
export declare class HttpExceptionFilter implements ExceptionFilter<HttpException> {
    private readonly logger;
    catch(exception: HttpException, host: ArgumentsHost): void;
}
