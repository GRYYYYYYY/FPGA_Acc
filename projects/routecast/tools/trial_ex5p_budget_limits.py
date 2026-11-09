"""Real frozen-prefix repair/label exhaustion with no route publication."""
import copy,json,time
from pathlib import Path
from collections import Counter,defaultdict
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from budget_repair_engine import repair_budget
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_budget_limits_2026-10-06';out.mkdir();parent=root/'experiments/ex5p_bounded_history_repair_2026-10-06';prior=json.loads((parent/'receipt.json').read_text());proof=json.loads((parent/'verification.json').read_text());assert proof['receipt_sha256']==sha(parent/'receipt.json');ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json'
p={'parent_sha256':sha(parent/'receipt.json'),'endpoint_sha256':sha(ep),'cases':[{'max_repairs':0,'max_labels':10000},{'max_repairs':4,'max_labels':1}],'source_hashes':{n:sha(root/'tools'/n) for n in ('budget_repair_engine.py','persistent_rc_context.py')},'scope':'Frozen real1898-prefix resource exhaustion; no routing input changes, no complete/native publication claim.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');ctx=PersistentRCContext(ep);saved=copy.deepcopy(prior);rows=[]
for case in p['cases']:
 start=time.monotonic();r=repair_budget(ctx,prior,**case);elapsed=time.monotonic()-start
 assert prior==saved and r['status']=='INCOMPLETE_NOT_PUBLISHABLE' and r['completed_connections']==1898 and r['repairs']==0
 assert r['records']==prior['records'] and r['failure']['query']==prior['failure']['query']
 assert {str(n):c for n,c in r['ledger'].items()}==prior['ledger'] and {str(n):c for n,c in r['history'].items()}==prior['history']
 assert len(r['events'])==1 and not r['events'][0]['committed']
 rows.append({'case':case,'wall_s':elapsed,'result':r})
assert rows[0]['result']['failure']['status']=='UNREACHABLE'
assert rows[1]['result']['failure']['status']=='LABEL_LIMIT'
# Independently rebuild retained unions from original XML, not engine slot tables.
endpoint=json.loads(ep.read_text());graph=Path(endpoint['inputs']['graph']['path']);edges=list(ET.parse(graph).getroot().find('rr_edges'));unions=defaultdict(set)
for rec in prior['records']:
 node=rec['source'];used={node}
 for eid in rec['answer']['physical_edge_ids']:
  edge=edges[eid];assert int(edge.get('src_node'))==node;node=int(edge.get('sink_node'));used.add(node)
 assert node==rec['sink'];unions[rec['net_id']].update(used)
ledger=Counter(n for used in unions.values() for n in used)
assert dict(ledger)=={int(n):c for n,c in prior['ledger'].items()}
ctx.reset();assert not ctx.history and not any(ctx.native.other)
r={'cases':rows,'retained_XML_ledger_verified':True,'caller_prior_unchanged':True,'failed_queries_not_committed':True,'reset_verified':True,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print([(x['case'],x['result']['failure']['status'],x['result']['completed_connections']) for x in rows])
