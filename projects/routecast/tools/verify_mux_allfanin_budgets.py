"""Independent reverse evaluation of all-fanin budgets with fixed retained paths."""
import json
from fractions import Fraction
from functools import lru_cache
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_allfanin_budgets_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json')and len(r['rows'])==12;rows=[]
for c,row in zip(p['cases'],r['rows']):
 w,i=c['width'],c['index'];f=out/f'w{w}_m{i}.json';assert sha(f)==row['sha256'];d=json.loads(f.read_text());tgfile=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mp=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgfile)==d['graph_sha256']and sha(mp)==d['mapping_sha256'];tg=json.loads(tgfile.read_text());m=json.loads(mp.read_text());incoming=defaultdict(list)
 for eid,e in tg['edges'].items():
  if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
 def evaluate(v):
  @lru_cache(None)
  def arrival(n):return max((arrival(u)+(v[int(d['edge_connection_ids'][eid])]/10**9+Fraction(m['external_edges'][eid]['old_local_offset_seconds'])if eid in d['edge_connection_ids']else Fraction(tg['edges'][eid]['max_delay_seconds']))for u,eid in incoming[n]),default=Fraction(0))
  return max(arrival(int(n))for n,k in tg['nodes'].items()if k=='SINK')*10**9
 floor={int(cid):Fraction(v)for cid,v in d['floor_ns'].items()};assert evaluate(floor)==Fraction(d['model_floor_cpd_ns']);affected=set(d['affected']['affected_complete_net_connection_ids']);old={}
 for eid,entry in m['external_edges'].items():
  cid=int(d['edge_connection_ids'][eid]);value=Fraction(entry['branch']['rr_delay_seconds'])*10**9;assert cid not in old or old[cid]==value;old[cid]=value
 assert set(old)==set(floor);assert all(floor[cid]==v for cid,v in old.items()if cid not in affected)
 if d['status']=='ALLFANIN_VECTOR_CONSTRUCTED':
  b={int(cid):Fraction(v)for cid,v in d['budgets_ns'].items()};assert all(b[cid]>=v for cid,v in floor.items());assert all(b[cid]<=1 for cid in affected);assert all(b[cid]==v for cid,v in old.items()if cid not in affected);assert evaluate(b)==Fraction(d['model_budget_cpd_ns'])<=Fraction(d['target_cpd_ns'])
 else:assert not d['budgets_ns']and(evaluate(floor)>Fraction(d['target_cpd_ns'])or any(floor[cid]>1 for cid in affected))
 rows.append(dict(width=w,index=i,status=d['status'],fixed_retained_over_1ns=sum(v>1 for cid,v in old.items()if cid not in affected)))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='All12 exact maxplus constraints independently reverseevaluated; retainedactualRR fixed,1nscap affectedonly. Native diagnosticminimum optimality not independently proven forrejections; localcarry hypothesis only.'),indent=2)+'\n');print(rows)
