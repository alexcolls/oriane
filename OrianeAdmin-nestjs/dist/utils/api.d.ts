export interface ApiFilter {
    field: string;
    operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'ilike';
    value: string | number | boolean;
}
export declare function applyFilters(query: any, filters?: ApiFilter[]): any;
