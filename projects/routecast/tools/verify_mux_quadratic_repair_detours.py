"""Verify archived shortest certificates without rerunning shortest solver."""
import json
from pathlib import Path
from fractions import Fraction as F
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_quadratic_repair_detours_2026-10-06';file=out/'receipt.json';d=json.loads(file.read_text());base=ROOT/'experiments/mux_quadratic_history_online_loop_2026-10-06';result=base/'w8_m1/result.json';assert d['result_sha256']==sha(result);p=json.loads((base/'protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(8,1));ctx=load_endpoints(case['target']);f=ctx[4].fields;inc=ctx[4].increments;scale=ctx[4].scale;source_of={s:u for u in range(len(ctx[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};data=json.loads(result.read_text());spec=data['allocations'][data['attempts'][0]['allocation_index']];assert spec['restrictions']=={};netids=set();labels=0
for row in d['rows']:
 q=row['query'];assert q in ctx[5];ban=set(row['forbidden']);assert ban=={4937};cert=row['certificate'];dist={int(k):v for k,v in cert['distances'].items()};pred={int(k):v for k,v in cert['predecessor_slots'].items()};source=q['source'];assert dist[source]==0 and set(pred)==set(dist)-{source} and not ban&dist.keys()
 for u,value in dist.items():
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if v not in ban and f['capacities'][v]>0:assert v in dist and dist[v]<=value+inc[s]
 rooted={source}
 for n in pred:
  trail=[];seen=set()
  while n not in rooted:
   assert n not in seen;seen.add(n);trail.append(n);s=pred[n];u=source_of[s];assert f['dest_ranks'][s]==n and dist[n]==dist[u]+inc[s];n=u
  rooted.update(trail)
 minimum=dist.get(q['sink']);budget=min(int(F(spec['budgets_ns'][str(q['connection_id'])])*scale/10**9),scale//10**9);assert row['minimum']==cert['minimum']==minimum and row['budget']==budget and minimum>budget;netids.add(q['net_id']);labels+=len(dist)
ep=json.loads(Path(case['target']).read_text());xml=ImmutableXMLAudit(ep['inputs']['graph']['path'],ep['graph_sha256']);assert xml.caps[4937]==1<len(netids)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(file),verifier_sha256=sha(Path(__file__)),result_sha256=sha(result),labels=labels,node=4937,capacity=1,mandatory_nets=sorted(netids),scope='Archived distance closure/all-edge inequalities/rooted predecessor checked without shortest solver. Original XML capacity and exact first-attempt budgets authenticated. Fixed additive integer-model allocation contradiction only; other allocations/global/nativeSTA infeasibility unproved.'),indent=2)+'\n');print('Verified archived fixed-budget contradiction',sorted(netids),labels)
