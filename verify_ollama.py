"""Compare the saved model-selected calls with current REST results."""
import argparse
import json
import os
from pathlib import Path
import settings
import httpx


def verify(audit_path, save):
    audit=json.loads(Path(audit_path).read_text())
    checks=json.loads((Path(audit_path).parent/'rest_vs_mcp.json').read_text())
    if not audit.get('completed') or not checks.get('passed'):
        raise SystemExit('Model run or source/REST/MCP checks are incomplete')
    comparison={'completed':True,'dataset_sha256':checks['dataset_sha256'],'tool_results':[]}
    with httpx.Client(timeout=15) as http:
        for call in audit['tool_calls']:
            name=call['name']
            if name=='search_shipwrecks':url=os.getenv('MONGO_API_URL','http://127.0.0.1:5001')+'/shipwrecks'
            elif name=='get_statistics':url=os.getenv('REDIS_API_URL','http://127.0.0.1:5002')+'/stats'
            else:raise SystemExit('Unexpected tool in model trace')
            response=http.get(url,params=call['arguments'])
            comparison['tool_results'].append({'tool':name,'selected_arguments':call['arguments'],
                'matches_direct_data':response.status_code==200 and response.json()==call['result']})
    names={r['tool'] for r in comparison['tool_results']}
    comparison['passed']=names=={'search_shipwrecks','get_statistics'} and all(r['matches_direct_data'] for r in comparison['tool_results'])
    Path(save).write_text(json.dumps(comparison,indent=2)+'\n')
    print(json.dumps(comparison,indent=2))
    if not comparison['passed']:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit',default='results/ollama.json')
    p.add_argument('--save',default='results/ollama_comparison.json')
    a=p.parse_args();verify(a.audit,a.save)
