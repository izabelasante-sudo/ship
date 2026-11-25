"""Read-only MCP tools that wrap the two Flask REST services."""
import os
from settings import allowed_statistics
from search_validation import search_query
import httpx
from mcp.server.mcpserver import MCPServer

mcp = MCPServer('Shipwreck data lab')
MONGO_API = os.getenv('MONGO_API_URL', 'http://127.0.0.1:5001')
REDIS_API = os.getenv('REDIS_API_URL', 'http://127.0.0.1:5002')


async def get_json(url: str, params: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise ValueError(f'REST service returned HTTP {exc.response.status_code}') from None
    except (httpx.HTTPError, ValueError):
        raise ValueError('REST service is unavailable or returned invalid JSON') from None


@mcp.tool()
async def search_shipwrecks(feature_type: str = '', water_level: str = '', limit: int = 3) -> dict:
    """Search MongoDB shipwreck records by exact category and/or water level (case-insensitive). Examples: feature_type='Wrecks - Visible' or 'Wrecks - Submerged, dangerous'; water_level='always dry'. Empty filters match all. limit is 1 to 20, default 3. Returns a sample and matched_count, not every matching record. Depth units are unspecified; zero/unknown depth is not a confirmed measurement."""
    search_query(feature_type, water_level, limit)
    return await get_json(f'{MONGO_API}/shipwrecks', {'feature_type': feature_type, 'water_level': water_level, 'limit': limit})


@mcp.tool()
async def get_statistics(key: str) -> dict:
    """Read Redis counts calculated from the complete supplied shipwrecks.json. key='shipwreck_summary' returns total records, counts by feature type and depth-quality counts. key='water_level_counts' returns counts by water level. These are dataset records, not live app users or global wreck totals."""
    if key not in allowed_statistics():
        raise ValueError('key is not allowed')
    return await get_json(f'{REDIS_API}/stats', {'key': key})


if __name__ == '__main__':
    mcp.run(transport='streamable-http', host='127.0.0.1', port=5000, stateless_http=True, json_response=True)
