import { Repository } from 'typeorm';
import { AwsSqsService } from '../../aws/aws.sqs.service';
import { HikerApiClientService } from '../hiker-api-client/hiker-api-client.service';
import { SearchAccountJob } from '../../entities/search-account-job.entity';
import { SearchAccountResult } from '../../entities/search-account-result.entity';
import { SearchAccountsByKeywordDto } from './dto/search-accounts.dto';
import { BulkSearchAccountsDto, BulkSearchResponseDto, SearchJobStatusDto, CsvSearchAccountsDto } from './dto/bulk-search-accounts.dto';
export declare class SearchAccountsService {
    private readonly hikerApiService;
    private readonly searchJobRepository;
    private readonly searchResultRepository;
    private readonly searchSqsService;
    private readonly logger;
    constructor(hikerApiService: HikerApiClientService, searchJobRepository: Repository<SearchAccountJob>, searchResultRepository: Repository<SearchAccountResult>, searchSqsService: AwsSqsService);
    searchAccountsByKeyword(dto: SearchAccountsByKeywordDto): Promise<SearchAccountResult[]>;
    startBulkSearch(dto: BulkSearchAccountsDto): Promise<BulkSearchResponseDto>;
    startCsvSearch(file: Express.Multer.File, dto: CsvSearchAccountsDto): Promise<BulkSearchResponseDto>;
    private parseKeywordsFromCsv;
    healthCheck(): Promise<any>;
    getJobStatus(searchAccountsId: string): Promise<SearchJobStatusDto>;
    generateCsvForJob(searchAccountsId: string): Promise<string>;
}
