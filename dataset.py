"""Read and summarize the supplied file without changing its records."""
import hashlib
import json
from collections import Counter
from pathlib import Path

DATA_PATH = Path(__file__).parent / 'data' / 'shipwrecks.json'
PROJECTION = {'_id': 1, 'feature_type': 1, 'latdec': 1, 'londec': 1, 'depth': 1, 'quasou': 1, 'watlev': 1}
DEPTH_NOTE = 'Depth values are reproduced as stored. Zero or unknown values are not confirmed measured depths; units are not supplied in this file.'


def load_dataset(path=DATA_PATH):
    raw = Path(path).read_bytes()
    rows = json.loads(raw)
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected a nonempty JSON array')
    ids = [r['_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate _id values in source dataset')
    for r in rows:
        if not isinstance(r['_id'], str) or not isinstance(r['feature_type'], str):
            raise ValueError('Invalid record identifier or category')
        if r['coordinates'] != [r['londec'], r['latdec']]:
            raise ValueError('Coordinate order must be longitude, latitude')
        if not (-180 <= r['londec'] <= 180 and -90 <= r['latdec'] <= 90):
            raise ValueError('Invalid geographic coordinate')
    return rows, hashlib.sha256(raw).hexdigest()


def statistics(rows, sha256):
    feature_counts = dict(sorted(Counter(r['feature_type'] or '(unspecified)' for r in rows).items()))
    water_counts = dict(sorted(Counter(r['watlev'] or '(unspecified)' for r in rows).items()))
    common = {'source': 'shipwrecks.json', 'source_sha256': sha256, 'total_records': len(rows)}
    return {
        'shipwreck_summary': {**common, 'feature_type_counts': feature_counts,
            'depth_unknown_records': sum(r['quasou'] == 'depth unknown' for r in rows),
            'zero_depth_records': sum(r['depth'] == 0 for r in rows), 'depth_note': DEPTH_NOTE},
        'water_level_counts': {**common, 'water_level_counts': water_counts},
    }


def projected(row):
    return {key: row[key] for key in PROJECTION if key in row}


if __name__ == '__main__':
    rows, digest = load_dataset()
    values = statistics(rows, digest)
    (DATA_PATH.parent / 'redis_stats.json').write_text(json.dumps(values, indent=2) + '\n')
    (DATA_PATH.parent / 'dataset_profile.json').write_text(json.dumps(values['shipwreck_summary'], indent=2) + '\n')
    print(json.dumps(values['shipwreck_summary'], indent=2))
