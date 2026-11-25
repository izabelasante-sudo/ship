"""Read-only Flask API for explicitly allowed Redis statistics keys."""

import json
import os
from settings import allowed_statistics

from flask import Flask, jsonify, request
import redis

app = Flask(__name__)
cache = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"), decode_responses=True, socket_timeout=3, socket_connect_timeout=3)


@app.get("/stats")
def statistics():
    key = request.args.get("key", "").strip()
    allowed = allowed_statistics()
    if key not in allowed:
        return jsonify(error="key is not allowed"), 400
    try:
        raw = cache.get(key)
    except redis.RedisError:
        app.logger.warning("Redis lookup failed; check local connection settings")
        return jsonify(error="database unavailable"), 503
    if raw is None:
        return jsonify(error="key not found"), 404
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw
    return jsonify(key=key, value=value)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
