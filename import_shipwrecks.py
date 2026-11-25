"""Import source records with a setup account; the app keeps read-only credentials."""
import os
import settings
from pymongo import MongoClient, ReplaceOne
from dataset import load_dataset

if __name__ == '__main__':
    rows, digest = load_dataset()
    client = MongoClient(os.getenv('SETUP_MONGO_URI', os.environ['MONGO_URI']), serverSelectionTimeoutMS=10000)
    collection = client[os.getenv('MONGO_DB', 'mcp_group_lab')][os.getenv('MONGO_COLLECTION', 'shipwrecks')]
    ids = {r['_id'] for r in rows}
    existing = {r['_id'] for r in collection.find({}, {'_id': 1})}
    if existing - ids:
        raise SystemExit('Target has records outside this file. Use a separate empty collection.')
    for offset in range(0, len(rows), 500):
        collection.bulk_write([ReplaceOne({'_id': r['_id']}, r, upsert=True) for r in rows[offset:offset+500]], ordered=False)
    collection.create_index([('feature_type', 1), ('_id', 1)])
    collection.create_index([('watlev', 1), ('_id', 1)])
    actual = {r['_id']: r for r in collection.find({})}
    assert actual == {r['_id']: r for r in rows}, 'Stored documents differ from source file'
    print('Imported and verified', len(actual), 'documents. Source SHA256:', digest)
