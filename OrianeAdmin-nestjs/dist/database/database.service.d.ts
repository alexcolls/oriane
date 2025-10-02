import { DataSource, QueryRunner } from 'typeorm';
export declare class DatabaseService {
    private readonly dataSource;
    constructor(dataSource: DataSource);
    executeQuery(query: string, parameters?: any[]): Promise<any>;
    startTransaction(): Promise<QueryRunner>;
    commitTransaction(queryRunner: QueryRunner): Promise<void>;
    rollbackTransaction(queryRunner: QueryRunner): Promise<void>;
}
