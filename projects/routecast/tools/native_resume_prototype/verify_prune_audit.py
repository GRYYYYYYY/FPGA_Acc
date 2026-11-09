"""Verify ordered before/after/routed tree snapshots for the diagnosed sink."""
import json,sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_prune_audit_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());pp=out/'protocol.json';p=json.loads(pp.read_text())
assert r['protocol_sha256']==sha(pp) and all(sha(f)==h for f,h in p['bindings'].items())
for row in r['rows']:assert all(sha(f)==h for f,h in row['files'].items())
q=next(row for row in r['rows'] if row['width']==16 and row['mode']=='workflow');states=defaultdict(dict)
for x in q['events']:
 if x[0]=='RC_PRUNE':
  key=x[1],int(x[2]);node=int(x[6]);assert node not in states[key];states[key][node]=dict(parent=int(x[5]),pin=int(x[4]),occ=int(x[7]),tdel_seconds=x[8])
def chain(tree):
 result=[];n=4018
 while n>=0:
  assert n in tree and n not in result;result.append(n);n=tree[n]['parent']
 return result[::-1]
rows=[]
for it in range(2,13):
 a,b,c=[states[stage,it] for stage in ('before','after','routed')];assert a and b and c
 assert 4018 in a and 4018 not in b and 4018 in c and c[4018]['pin']==9
 before,after=chain(a),chain(c)
 rows.append(dict(iteration=it,before_nodes=len(a),after_prune_nodes=len(b),routed_nodes=len(c),retained_sinks=sum(v['pin']>0 for v in b.values()),before_chain=before,routed_chain=after,retained_chain_nodes=[n for n in before if n in b],removed_chain_nodes=[n for n in before if n not in b],same_node_chain=before==after,routed_sink_delay_seconds=c[4018]['tdel_seconds']))
assert all(x['same_node_chain'] and len(x['retained_chain_nodes'])==5 and x['removed_chain_nodes']==[4060,4018] for x in rows if x['iteration']>=6)
selected=[x for x in q['events'] if x[0]=='RC_FORCE_SELECT' and x[2]=='s6_0' and x[3]=='9'];assert len(selected)==8
result=dict(receipt_sha256=sha(rp),verifier_sha256=sha(Path(__file__)),rows=rows,target_forced_selection_events=selected,scope='Native private instrumentation, all four final full paths equal proven tol101 controls. Target sink removed each setup iteration; seven late iterations retain five chain nodes and reconstruct same node chain. Intermediate switch identity not logged; global occupancy includes all nets; no causal proof or performance claim.')
(out/'prune_verification.json').write_text(json.dumps(result,indent=2)+'\n');print('Verified sink removal and repeated node chain in iterations6..12.')
