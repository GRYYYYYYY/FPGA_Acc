"""Identify frozen mandatory owners blocking the prior budget-feasible witness."""
import json,xml.parsers.expat as X
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_residual_release_diagnostic_v1_2026-10-21';D.mkdir(exist_ok=True)
P=R/'experiments/mmc_cover_residual_avoidance_v2_2026-10-21/case_03/NET_142/result.json';C=R/'experiments/mmc_cover_budget_avoidance_v1_2026-10-21/case_03/NET_142/result.json';B=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/case_03/banks.jsonl';V=R/'experiments/mmc_bank_mandatory_capacity_v1_2026-10-21/verification.json'
v=json.loads(V.read_text());row=next(r for r in v['rows'] if r['case']=='case_03');chosen={n for c in row['owner_conflict_components'] for n in c['cover']};bad=json.loads(P.read_text());prior=json.loads(C.read_text());fail=[q for q in bad['connections'] if not q['within_budget']];assert len(fail)==1
q=next(q for q in prior['connections'] if q['connection_id']==fail[0]['connection_id']);assert q['within_budget'];wanted=set(q['physical_edge_ids']);arcs={};stack=[];eid=0
G=Path(json.loads(Path(row['endpoint']).read_text())['inputs']['graph']['path']);bindings={str(p):sha(p) for p in [P,C,B,V,G,Path(__file__)]}
def opening(tag,a):
 global eid
 if tag=='edge' and stack and stack[-1]=='rr_edges':
  if eid in wanted:arcs[eid]=(int(a['src_node']),int(a['sink_node']))
  eid+=1
 stack.append(tag)
def closing(tag):assert stack.pop()==tag
parser=X.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
with G.open('rb') as f:
 while b:=f.read(8*1024*1024):parser.Parse(b,False)
parser.Parse(b'',True);assert set(arcs)==wanted
node=q['source'];nodes={node}
for e in q['physical_edge_ids']:
 a,b=arcs[e];assert a==node;node=b;nodes.add(b)
assert node==q['sink'];blocked=nodes&set(bad['blocked_nodes']);owners=defaultdict(list)
for line in B.open():
 bank=json.loads(line)
 if bank['net_id'] not in chosen:
  for n in blocked&set(bank['A'])&set(bank['B']):owners[n].append(bank['net_id'])
assert set(owners)==blocked
out={'status':'PRIOR_BUDGET_FEASIBLE_PATH_BLOCKERS_IDENTIFIED','failed_connection':fail[0]['connection_id'],'prior_minimum':q['minimum'],'original_budget':q['budget'],'residual_minimum':fail[0]['minimum'],'blocking_channels':dict(owners),'additional_NETs_to_release_this_specific_path':sorted({net for ns in owners.values() for net in ns}),'scope':'Necessary releases for this one archived path under fixed cover; not a minimum release set over all paths or a joint feasible routing. Releasing owners requires new complete budget-admissible trees; costs and full capacity remain unproven.','bindings':bindings}
assert all(sha(p)==h for p,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:x for k,x in out.items() if k!='bindings'},indent=2))
