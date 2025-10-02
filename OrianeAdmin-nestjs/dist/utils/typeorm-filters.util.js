"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.applyTypeOrmFilters = applyTypeOrmFilters;
function applyTypeOrmFilters(queryBuilder, entityAlias, filters) {
    if (filters && filters.length > 0) {
        filters.forEach((filter, index) => {
            const fieldPath = `${entityAlias}.${filter.field}`;
            const parameterName = `${filter.field.replace(/\./g, '_')}_${index}`;
            let condition;
            let parameterValue = filter.value;
            switch (filter.operator) {
                case 'eq':
                    condition = `${fieldPath} = :${parameterName}`;
                    break;
                case 'neq':
                    condition = `${fieldPath} != :${parameterName}`;
                    break;
                case 'gt':
                    condition = `${fieldPath} > :${parameterName}`;
                    break;
                case 'gte':
                    condition = `${fieldPath} >= :${parameterName}`;
                    break;
                case 'lt':
                    condition = `${fieldPath} < :${parameterName}`;
                    break;
                case 'lte':
                    condition = `${fieldPath} <= :${parameterName}`;
                    break;
                case 'like':
                    condition = `${fieldPath} LIKE :${parameterName}`;
                    parameterValue = `%${filter.value}%`;
                    break;
                case 'ilike':
                    condition = `${fieldPath} ILIKE :${parameterName}`;
                    parameterValue = `%${filter.value}%`;
                    break;
                default:
                    console.warn(`Unsupported filter operator: ${filter.operator}`);
                    return;
            }
            queryBuilder
                .andWhere(condition)
                .setParameter(parameterName, parameterValue);
        });
    }
    return queryBuilder;
}
//# sourceMappingURL=typeorm-filters.util.js.map