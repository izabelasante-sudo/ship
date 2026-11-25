"""Refresh only the two dedicated lab keys using the supplied dataset."""
import json
import os
import settings
import redis
from dataset import load_dataset, statistics

if __name__ == '__main__':
    rows, digest = load_dataset()
    values = statistics(rows, digest)
    cache = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://127.0.0.1:16380/0'), socket_timeout=3)
    with cache.pipeline(transaction=True) as pipe:
        for key, value in values.items():
            pipe.set(key, json.dumps(value))
        pipe.execute()
    print('Updated shipwreck_summary and water_level_counts from', len(rows), 'source records')
