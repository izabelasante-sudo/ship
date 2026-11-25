# MCP Shipwreck Data Lab

This project connects Ollama qwen3:4b to the supplied shipwrecks.json through MongoDB Atlas, Redis, two Flask APIs and MCP. MongoDB stores all 11,095 source documents. Redis stores counts calculated from that same file. The original file is included unchanged in data/shipwrecks.json.

## Report and presentation

- [Download the Word report](REPORT.docx)
- [Download the five-slide PowerPoint](MCP_Shipwreck_Presentation.pptx)
- [Read the report online](REPORT.md)
- [Presentation guide](PRESENTATION.md)

## Architecture

User question -> Ollama Python client -> MCP server on localhost:5000/mcp -> Flask APIs -> databases.

- search_shipwrecks(feature_type, water_level, limit) calls GET /shipwrecks on port 5001 and reads MongoDB.
- get_statistics(key) calls GET /stats on port 5002 and reads the separate Redis instance on port 16380.
- Redis permits shipwreck_summary and water_level_counts. These are dataset summaries, not application telemetry.

## Dataset and interpretation

The file contains 6,578 dangerous submerged wreck records, 2,585 visible wreck records, 1,845 nondangerous submerged wreck records, 23 distributed-remains records and 64 records with an empty feature type. These total 11,095. Blank feature types are shown as (unspecified) in summaries; stored documents keep the original empty string.

The fields include _id, feature_type, chart, latitude (latdec), longitude (londec), depth, water level (watlev), depth quality (quasou) and coordinates in [longitude, latitude] order. Original string identifiers, categories and numbers are preserved. Many descriptive fields are empty. The file does not provide depth-unit metadata: 8,520 records contain depth=0 and 5,573 have quasou="depth unknown". These groups overlap and must not be added. Do not interpret zeros as confirmed measurements or invent vessel names, dates or depth units. Counts describe this supplied file, not every wreck worldwide.

## Setup on another computer

1. Create a Python environment and install requirements.txt. Copy .env.example to .env and fill in connection settings. LAB_ENV_FILE can point to a private configuration outside this directory.

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
~~~

2. In Atlas, create mcp_group_lab.shipwrecks and insert data/shipwrecks.json as a JSON array. Alternatively, run python import_shipwrecks.py using a setup account supplied through SETUP_MONGO_URI. The importer verifies the complete stored content and refuses a collection containing unrelated identifiers. It can refresh records from this source and creates optional search indexes. The application should use a separate account with only the read role on mcp_group_lab. Do not distribute credentials.

3. Start a dedicated Redis instance on localhost port 16380, then populate the two lab summary keys:

~~~bash
mkdir -p redis-data
redis-server --bind 127.0.0.1 --port 16380 --protected-mode yes --appendonly yes --dir ./redis-data
~~~

In another terminal with the Python environment activated:

~~~bash
python dataset.py
python seed_redis.py
~~~

The seeder recalculates counts from the source file and refreshes only shipwreck_summary and water_level_counts. Re-run it after an intentional dataset update. Verification detects mismatches between the source, MongoDB and Redis.

4. Ensure Ollama is running and ollama list includes qwen3:4b. Start the Flask and MCP services:

~~~bash
python run_lab.py
~~~

## Run and verify

In another terminal, activate the environment and run:

~~~bash
curl 'http://127.0.0.1:5001/shipwrecks?feature_type=Wrecks%20-%20Visible&limit=3'
curl 'http://127.0.0.1:5002/stats?key=shipwreck_summary'
python mcptest.py
python verify_pipeline.py --save results/rest_vs_mcp.json
python ollama_client.py --save results/ollama.json
python verify_ollama.py
~~~

Default question: "Show three visible shipwreck records with their locations, and give the total number of records and counts by feature type in the shipwreck dataset."

The direct search returns three records and matched_count=2585. This distinguishes the returned sample from all matching records. The Redis summary contains total_records=11095 and all five feature-type counts. The model chooses its tools from their descriptions. Its Python host executes those tools and passes their actual results back to Qwen. Local inference can take several minutes; use the saved results for a short presentation.

verify_pipeline.py checks all stored MongoDB documents against the file, REST/MCP equality, both Redis summaries against locally computed counts, invalid limits, long filters, disallowed keys, literal regular-expression characters, empty results and combined case-insensitive filters. verify_ollama.py compares each model-selected call with the corresponding current REST result. Review the final model answer separately for correct meaning.

## Files and presentation

- data/shipwrecks.json: unchanged supplied dataset.
- data/redis_stats.json and dataset_profile.json: derived counts and source checksum.
- dataset.py, import_shipwrecks.py, seed_redis.py: loading and reproducible setup.
- mongo_api.py, redis_api.py, search_validation.py: database access and argument validation.
- mcp_server.py, mcptest.py, ollama_client.py: MCP tools and clients.
- verify_pipeline.py, verify_ollama.py: source and integration checks.
- results/: recorded tests, actual model output, result figures.
- REPORT.docx and REPORT.md: project report.
- MCP_Shipwreck_Presentation.pptx and PRESENTATION.md: five-slide deck and presentation guide.

## Security and limitations

Application services bind to localhost. MongoDB uses a read-only application account. Search values are escaped, matched literally and capped at 80 characters; results are limited to 20 records with fixed output fields and deterministic ordering. Queries have a 2-second time limit. Redis permits only the two summary keys. Timeouts, model-call budgets and duplicate-call caching bound a single client request.

This is a local classroom demo with Flask development servers and unauthenticated local Redis. A shared deployment needs authentication, authorization, server-side rate/concurrency limits, TLS and monitoring. Client budgets are not a server-side rate limit. Source-file equality verifies faithful loading, not the accuracy or completeness of the original observations. No real-world navigation or global wreck-total claims are made.

If MongoDB returns 503, check the Atlas current-IP entry, read role, URI and collection. If Redis returns 503, start the dedicated instance. When changing files, restart the three application services. Never include .env or private setup credentials in a submission.
