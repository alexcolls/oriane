import { SelectQueryBuilder } from 'typeorm';
import { ApiFilter } from './api';
export declare function applyTypeOrmFilters<T>(queryBuilder: SelectQueryBuilder<T>, entityAlias: string, filters?: ApiFilter[]): SelectQueryBuilder<T>;
