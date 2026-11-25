# MCP Shipwreck Data Lab

This project connects a local Ollama Qwen3:4b model to shipwreck data through the Model Context Protocol (MCP). MongoDB stores the supplied records, and Redis stores summaries calculated from the same dataset. Two Flask REST services provide database access, while MCP exposes discoverable tools that the model can select from a natural-language question.

The completed checks confirmed that all 11,095 MongoDB documents match the supplied file. REST and MCP returned identical results, both Redis summaries matched counts calculated from the source, and the recorded Qwen run selected both database tools successfully.

## Project objective

The demonstration answers a combined request: show three visible shipwreck records with their locations, then report the dataset total and the counts for each feature type. This requires retrieving individual records from MongoDB and summary data from Redis. The application preserves the distinction between a returned sample, the number of matching records and the total dataset size.

## Dataset and category counts

The input is shipwrecks.json, a JSON array containing 11,095 records with 11,095 unique string identifiers. The project retains the supplied file unchanged. The following counts were calculated from that file and verified against the stored data.

| Feature type | Records |
| --- | --- |
| Wrecks - Submerged, dangerous | 6,578 |
| Wrecks - Visible | 2,585 |
| Wrecks - Submerged, nondangerous | 1,845 |
| (unspecified) | 64 |
| distributed remains of wreck | 23 |
| Total | 11,095 |

## Fields and data quality

Each record includes feature_type, chart, latitude (latdec), longitude (londec), depth, water level (watlev), depth quality (quasou) and coordinates. The coordinates array stores longitude before latitude. String identifiers, original values and empty fields are preserved in MongoDB. The summary uses (unspecified) for the 64 empty feature-type values, without changing the source records.

There are 8,520 records whose depth value is zero and 5,573 marked depth unknown. These groups overlap and must not be added. The file does not specify depth units, so zero values are not treated as confirmed measurements and no unit is inferred. Many vessel-description and history fields are empty. Dataset totals describe the supplied records rather than a complete global inventory of shipwrecks.

## Procedure and implementation

## Service architecture

| Component | Role |
| --- | --- |
| Ollama Qwen3:4b | Selects tools from their descriptions and produces the final answer from returned data. |
| Python client | Discovers tools, executes selected calls and records arguments, results, the answer and timing. |
| MCP server on port 5000 | Exposes search_shipwrecks and get_statistics over Streamable HTTP at /mcp. |
| Flask on port 5001 | GET /shipwrecks reads mcp_group_lab.shipwrecks in MongoDB Atlas. |
| Flask on port 5002 | GET /stats reads allowed summary keys from the dedicated Redis instance on port 16380. |

## Data loading

The complete JSON array was imported into mcp_group_lab.shipwrecks through Atlas. The application continues to use a MongoDB account with the read role scoped to the lab database. Verification fetched every stored document and compared its fields and values with the original record sharing the same identifier.

The Redis seeder recalculates shipwreck_summary and water_level_counts from the supplied file. The first key contains the total, feature-type counts and depth-quality counts. The second contains water-level counts. Both carry the source filename and its SHA-256 checksum. The seeder updates only these two lab keys, making the summaries reproducible. A later source change requires reloading MongoDB and reseeding Redis before rerunning verification.

## Search and tool behavior

search_shipwrecks accepts optional feature_type and water_level filters, plus an integer limit from 1 to 20. Nonempty filters use exact case-insensitive matching with regular-expression characters escaped. Results are sorted by identifier and contain only explicitly selected fields. The response reports count for returned records and matched_count for all records satisfying the filters.

get_statistics accepts only the two approved Redis keys. The MCP tools reuse the Flask APIs instead of opening database connections directly. The Python client converts discovered MCP schemas into Ollama tool definitions, executes the model-selected calls and supplies their actual results to the model.

## Reproduction

The README explains configuration, importing the dataset and starting MongoDB access, Redis and Ollama. With the services running, the following commands reproduce the checks and model demonstration.

~~~bash
python mcptest.py
python verify_pipeline.py --save results/rest_vs_mcp.json
python ollama_client.py --save results/ollama.json
python verify_ollama.py
~~~

## Observed results and comparison

## Source and integration checks

The recorded checks used the actual MongoDB Atlas collection and the separate local Redis instance. The complete verification report is saved in results/rest_vs_mcp.json.

| Check | Observed result |
| --- | --- |
| MongoDB against the source | All 11,095 stored documents matched the original file by identifier and full document contents. |
| Visible wreck search | REST and MCP both returned three records, matched_count 2,585 and identical JSON. The returned sample matched the source. |
| Redis feature summary | REST and MCP returned identical JSON with total_records 11,095 and all five category counts. The values matched counts recomputed from the file. |
| Redis water-level summary | REST and MCP returned identical JSON. All water-level counts matched the source. |
| Invalid inputs | Limits 0 and 21, an 81-character filter and two disallowed Redis keys were rejected by both REST and MCP. REST returned HTTP 400. |
| Literal and combined filters | The text .* was treated literally. An unknown category returned an empty result. Combined category and water-level filters matched the source case-insensitively. |
| Overall verification | passed: true. |

## Example MongoDB records

For feature_type="Wrecks - Visible" and limit=3, the following records were returned in identifier order. All three have watlev="always dry". Coordinates are shown in separate latitude and longitude columns to make their order explicit.

| Record identifier | Latitude | Longitude |
| --- | --- | --- |
| 578f6fa2df35c7fbdbaed8c4 | 9.3547792 | -79.9081268 |
| 578f6fa2df35c7fbdbaed8c5 | 9.3340302 | -79.9357223 |
| 578f6fa2df35c7fbdbaed8c7 | 9.3390503 | -79.9137115 |

## Meaning of the results

The value 3 is the size of this returned sample. The value 2,585 counts all visible wreck records, while 11,095 counts every record in the file. The feature-type counts sum to 11,095. The Redis and MongoDB outputs describe the same underlying dataset, so they should not be treated as separate populations or added together.

Full-record equality establishes faithful loading and retrieval. It does not validate the accuracy, age or completeness of the original observations. The tests cover representative filtering and error cases, not every possible query or production load.

## Model selection and answer

## Demonstration question

Show three visible shipwreck records with their locations, and give the total number of records and counts by feature type in the shipwreck dataset.

## Recorded tool calls

The saved successful run selected the following tools and arguments. These lines come from results/ollama.json.

~~~text
search_shipwrecks({"feature_type": "Wrecks - Visible", "limit": 3})
get_statistics({"key": "shipwreck_summary"})
~~~

## Result verification

The model-selected search returned the requested record sample and the statistics lookup returned the summary for the full dataset. verify_ollama.py repeated the corresponding REST calls using the model's actual arguments. Every saved tool result matched the current REST response, and both required tools appeared in the trace. The comparison is recorded in results/ollama_comparison.json with passed: true.

## Final model response

Three visible shipwreck records with locations:
1. Latitude: 9.3547792, Longitude: -79.9081268
2. Latitude: 9.3340302, Longitude: -79.9357223
3. Latitude: 9.3390503, Longitude: -79.9137115

Dataset summary:
- Total records: 11,095
- Feature type counts: 
  - Wrecks - Visible: 2,585
  - Wrecks - Submerged, dangerous: 6,578
  - Wrecks - Submerged, nondangerous: 1,845
  - Distributed remains of wreck: 23
  - (unspecified): 64

Note: Zero depth values in records are not confirmed measurements per dataset documentation.

## Runtime and presentation

Ollama reported a combined model duration of 404.8 seconds across 2 rounds, approximately 6 minutes 45 seconds. This sum measures the model-reported round durations, not the complete wall-clock time of the demonstration. Local inference can take several minutes, so a short presentation can show the saved trace while direct MCP calls run live.

The client streams progress and treats incomplete or token-limited responses as errors. It allows up to 600 seconds per round, four rounds and eight total tool calls. The report uses the completed run that passed comparison.

## Security and conclusions

## Why MCP is useful alongside REST

REST provides service access. MCP adds tool discovery, descriptions, argument schemas and invocation. Flask continues to handle database access. Qwen selects operations, and its Python host performs the calls and returns the data. This implementation demonstrates MCP tools.

## Denial of service risk

Repeated prompts can generate repeated database queries. Read-only operations still consume CPU, memory, connections and model context. An accidental loop or concurrent clients could exhaust these resources. Small responses reduce model input size but do not prevent repeated requests.

| Implemented control | Purpose and scope |
| --- | --- |
| Localhost services and MongoDB read role | Restrict exposure and prevent application tools from modifying MongoDB records. Local processes can still reach the services. |
| Validated literal filters and fixed fields | Prevent users from supplying MongoDB operators or arbitrary projections through the exposed tools. |
| Result limit and query deadlines | Return at most 20 records and apply a 2-second MongoDB query limit with connection and socket timeouts. |
| Redis allowlist | Expose only shipwreck_summary and water_level_counts. |
| Client timeouts and budgets | Bound one question's model rounds, tool calls and duplicate work. These are not server-wide rate limits. |

## Shared deployment requirements

A shared service would need user authentication, per-tool authorization, server-side rate and concurrency limits, bounded queues, request-size limits, monitored timeouts and audit logs. TLS should protect network traffic. This local demonstration uses Flask development servers and a dedicated localhost Redis instance without authentication. It has not been load-tested as a production service.

Database strings remain untrusted data. The prompt tells Qwen to ignore embedded instructions, but this alone is not a complete defense. Narrow read-only tools, validated arguments and limited data access provide the enforced boundaries.

## Conclusion

The project retrieves the supplied shipwreck records through MongoDB and dataset summaries through Redis using a shared MCP interface. Full-source checks, REST/MCP comparisons and the completed Qwen trace agree on the tested results. The main lessons are to preserve dataset meaning, distinguish sample size from totals, retain missing-data limitations and verify model-selected tool results separately from the final prose.
