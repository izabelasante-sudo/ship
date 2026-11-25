"""Shared REST/MCP argument validation. Accept values, never query operators."""
import re


def search_query(feature_type='', water_level='', limit=3):
    if not isinstance(feature_type, str) or not isinstance(water_level, str):
        raise ValueError('Filters must be strings')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError('limit must be an integer from 1 to 20')
    query = {}
    for key, value in [('feature_type', feature_type), ('watlev', water_level)]:
        value = value.strip()
        if len(value) > 80:
            raise ValueError('Filters must contain at most 80 characters')
        if value:
            query[key] = {'$regex': '^' + re.escape(value) + '$', '$options': 'i'}
    return query, limit
