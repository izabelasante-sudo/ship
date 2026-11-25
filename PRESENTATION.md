# Five-slide presentation guide

## Slide 1  Project and architecture

Explain that one natural-language question retrieves individual shipwreck records from MongoDB and summary counts from Redis. Both databases use the same supplied file. Follow the diagram from Qwen and the Python host through MCP and Flask to the databases. The host executes the tools; Qwen selects them.

## Slide 2  Dataset results

Show the five feature-type counts and the total of 11,095. Explain that 64 blank feature types are retained as an unspecified category. The counts describe this file, not a complete world inventory. The source coordinates array uses longitude first. Avoid making claims about depth units.

## Slide 3  Database and integration evidence

Show the record excerpt from the MongoDB-backed query and the saved verification output. These PNGs render the verified saved results. Every imported document matched the supplied file. REST and MCP returned identical JSON. The visible-wreck search returns three example records from 2,585 matching records; the Redis summary covers all 11,095 records. Both Redis keys were checked against counts recomputed from the source.

## Slide 4  Qwen tool calls and answer

Read the question, show the actual selected arguments and then the saved answer excerpt. Explain that the integration check compares actual tool results, while the model's prose must also be inspected. The 6 min 45 sec figure is the sum of the model-reported durations for two rounds, not full wall-clock runtime. For a short presentation, use the saved trace rather than waiting for local inference.

## Slide 5  Security and data limitations

Repeated read-only tool calls can still overload services. Describe input validation, the result cap, read-only MongoDB access, timeouts and client call budgets. Shared deployment would need authentication and server-side throttling. There are 5,573 records marked depth unknown and 8,520 zero depth values; the groups overlap. Do not add these counts or interpret zero as a measured depth.

## Live demonstration commands

From this directory with the configured environment:

~~~bash
python mcptest.py
python verify_pipeline.py --save results/rest_vs_mcp.json
python ollama_client.py --save results/ollama.json
python verify_ollama.py
~~~

Use results/direct_mcp.txt and results/ollama_console.txt if a live run is too slow. Re-run verification when the source or database changes.
