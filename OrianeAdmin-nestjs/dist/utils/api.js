"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.applyFilters = applyFilters;
function applyFilters(query, filters) {
    if (filters && filters.length > 0) {
        filters.forEach((filter) => {
            switch (filter.operator) {
                case 'eq':
                    query = query.eq(filter.field, filter.value);
                    break;
                case 'neq':
                    query = query.neq(filter.field, filter.value);
                    break;
                case 'gt':
                    query = query.gt(filter.field, filter.value);
                    break;
                case 'gte':
                    query = query.gte(filter.field, filter.value);
                    break;
                case 'lt':
                    query = query.lt(filter.field, filter.value);
                    break;
                case 'lte':
                    query = query.lte(filter.field, filter.value);
                    break;
                case 'like':
                    query = query.like(filter.field, `%${filter.value}%`);
                    break;
                case 'ilike':
                    query = query.ilike(filter.field, `%${filter.value}%`);
                    break;
                default:
                    break;
            }
        });
    }
    return query;
}
//# sourceMappingURL=api.js.map