"""Read-only Flask API for the supplied shipwreck dataset in MongoDB."""
import os
import settings
from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dataset import PROJECTION, DEPTH_NOTE
from search_validation import search_query

app = Flask(__name__)
mongo = MongoClient(os.getenv('MONGO_URI', 'mongodb://127.0.0.1:27017'), serverSelectionTimeoutMS=5000, connectTimeoutMS=5000, socketTimeoutMS=5000)
collection = mongo[os.getenv('MONGO_DB', 'mcp_group_lab')][os.getenv('MONGO_COLLECTION', 'shipwrecks')]


@app.get('/shipwrecks')
def shipwrecks():
    try:
        if set(request.args) - {'feature_type', 'water_level', 'limit'} or any(len(request.args.getlist(k)) > 1 for k in request.args):
            raise ValueError('Unknown or repeated query parameter')
        query, limit = search_query(request.args.get('feature_type', ''), request.args.get('water_level', ''), int(request.args.get('limit', '3')))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    try:
        matched = collection.count_documents(query, maxTimeMS=2000)
        rows = list(collection.find(query, PROJECTION).sort('_id', 1).limit(limit).max_time_ms(2000))
        for row in rows:
            row['_id'] = str(row['_id'])
    except PyMongoError:
        app.logger.warning('MongoDB query failed; check local connection settings')
        return jsonify(error='database unavailable'), 503
    return jsonify(source='shipwrecks.json', count=len(rows), matched_count=matched, limit=limit, shipwrecks=rows, depth_note=DEPTH_NOTE)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
