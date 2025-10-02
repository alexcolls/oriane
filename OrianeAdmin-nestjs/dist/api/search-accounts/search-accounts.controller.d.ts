import { Response } from 'express';
import { SearchAccountsService } from './search-accounts.service';
import { SearchAccountsByKeywordDto } from './dto/search-accounts.dto';
import { BulkSearchAccountsDto, BulkSearchResponseDto, SearchJobStatusDto, CsvSearchAccountsDto } from './dto/bulk-search-accounts.dto';
export declare class SearchAccountsController {
    private readonly searchAccountsService;
    private readonly logger;
    constructor(searchAccountsService: SearchAccountsService);
    searchAccountsByKeyword(dto: SearchAccountsByKeywordDto): Promise<{
        success: boolean;
        data: {
            keyword: string;
            count: number;
            accounts: import("../../entities/search-account-result.entity").SearchAccountResult[];
        };
        message: string;
    }>;
    startBulkSearch(dto: BulkSearchAccountsDto): Promise<BulkSearchResponseDto>;
    startCsvSearch(file: Express.Multer.File, dto: CsvSearchAccountsDto): Promise<BulkSearchResponseDto>;
    getJobStatus(searchAccountsId: string): Promise<SearchJobStatusDto>;
    downloadResults(searchAccountsId: string, res: Response): Promise<void>;
}
