"""Read either structured MCP output or JSON in a text content block."""

import json


def payload(result):
    if result.structured_content is not None:
        return result.structured_content
    texts = [block.text for block in result.content if getattr(block, "type", None) == "text"]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return texts[0]
    return texts
