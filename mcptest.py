"""Discover and invoke MCP tools without any language model."""

import asyncio
import json
import os
import settings

from mcp import Client


async def main() -> None:
    async with Client(os.getenv("MCP_URL", "http://127.0.0.1:5000/mcp")) as client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")
        for name, arguments in [
            ("search_shipwrecks", {"feature_type": "Wrecks - Visible", "limit": 3}),
            ("get_statistics", {"key": "shipwreck_summary"}),
        ]:
            result = await client.call_tool(name, arguments)
            print(f"\n{name}({arguments}):")
            payload = result.structured_content
            if payload is None:
                texts = [block.text for block in result.content if hasattr(block, "text")]
                try:
                    payload = json.loads(texts[0]) if len(texts) == 1 else texts
                except json.JSONDecodeError:
                    payload = texts
            print(json.dumps(payload, indent=2))
            if result.is_error or (isinstance(payload, dict) and "error" in payload):
                raise RuntimeError(f"{name} failed: {payload}")


if __name__ == "__main__":
    asyncio.run(main())
