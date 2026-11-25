"""Verify source-file, MongoDB, Redis, REST and MCP agreement plus invalid inputs."""
import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import settings
import httpx
from pymongo import MongoClient
from mcp import Client
from mcp_results import payload
from dataset import load_dataset, statistics, projected, DEPTH_NOTE

DEMO_ARGS = {'feature_type': 'Wrecks - Visible', 'limit': 3}


async def main(save):
    rows, digest = load_dataset()
    expected_stats = statistics(rows, digest)
    source_by_id = {r['_id']: r for r in rows}
    mongo = MongoClient(os.environ['MONGO_URI'], serverSelectionTimeoutMS=5000)
    collection = mongo[os.getenv('MONGO_DB','mcp_group_lab')][os.getenv('MONGO_COLLECTION','shipwrecks')]
    stored = {str(r['_id']): {**r, '_id': str(r['_id'])} for r in collection.find({}).max_time_ms(5000)}
    source_match = stored == source_by_id
    mongo.close()
    visible = sorted([r for r in rows if r['feature_type'] == DEMO_ARGS['feature_type']], key=lambda r: r['_id'])
    expected_search = {'source': 'shipwrecks.json', 'count': 3, 'matched_count': len(visible), 'limit': 3,
                       'shipwrecks': [projected(r) for r in visible[:3]], 'depth_note': DEPTH_NOTE}
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'dataset_sha256': digest,
              'source_records': len(rows), 'mongo_records': len(stored), 'mongo_matches_source': source_match,
              'comparisons': [], 'validation': []}
    mongo_url = os.getenv('MONGO_API_URL','http://127.0.0.1:5001') + '/shipwrecks'
    redis_url = os.getenv('REDIS_API_URL','http://127.0.0.1:5002') + '/stats'
    async with Client(os.getenv('MCP_URL','http://127.0.0.1:5000/mcp')) as client, httpx.AsyncClient(timeout=15) as http:
        report['tools'] = [t.model_dump(mode='json') for t in (await client.list_tools()).tools]
        for tool, url, args, expected in [
            ('search_shipwrecks', mongo_url, DEMO_ARGS, expected_search),
            ('get_statistics', redis_url, {'key':'shipwreck_summary'}, {'key':'shipwreck_summary','value':expected_stats['shipwreck_summary']}),
            ('get_statistics', redis_url, {'key':'water_level_counts'}, {'key':'water_level_counts','value':expected_stats['water_level_counts']}),
        ]:
            rest = await http.get(url, params=args)
            result = await client.call_tool(tool,args)
            data = payload(result)
            report['comparisons'].append({'tool':tool,'arguments':args,'rest_status':rest.status_code,
                'rest':rest.json(),'mcp':data,'match':rest.status_code==200 and not result.is_error and rest.json()==data,
                'matches_source':data==expected})
        cases=[('search_shipwrecks',mongo_url,{'limit':0}),('search_shipwrecks',mongo_url,{'limit':21}),
               ('search_shipwrecks',mongo_url,{'feature_type':'x'*81}),('get_statistics',redis_url,{'key':'active_users'}),
               ('get_statistics',redis_url,{'key':'not_allowed'})]
        for tool,url,args in cases:
            result=await client.call_tool(tool,args)
            rest=await http.get(url,params=args)
            report['validation'].append({'tool':tool,'arguments':args,'rejected':result.is_error,'rest_status':rest.status_code})
        literal=payload(await client.call_tool('search_shipwrecks',{'feature_type':'.*','limit':20}))
        missing=payload(await client.call_tool('search_shipwrecks',{'feature_type':'NO SUCH TYPE','limit':3}))
        combined=payload(await client.call_tool('search_shipwrecks',{'feature_type':'wrecks - visible','water_level':'always dry','limit':2}))
        combined_expected=sorted([r for r in rows if r['feature_type'].lower()=='wrecks - visible' and r['watlev']=='always dry'],key=lambda r:r['_id'])
        report['filter_checks']={'regex_treated_literally':literal.get('matched_count')==0,
             'no_match_is_empty':missing.get('shipwrecks')==[] and missing.get('matched_count')==0,
             'combined_case_insensitive_filter':combined.get('matched_count')==len(combined_expected) and combined.get('shipwrecks')==[projected(r) for r in combined_expected[:2]]}
    report['passed'] = source_match and all(x['match'] and x['matches_source'] for x in report['comparisons']) and all(x['rejected'] and x['rest_status']==400 for x in report['validation']) and all(report['filter_checks'].values())
    Path(save).parent.mkdir(parents=True,exist_ok=True)
    Path(save).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('tools','comparisons')},indent=2))
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save',default='results/rest_vs_mcp.json')
    asyncio.run(main(parser.parse_args().save))
