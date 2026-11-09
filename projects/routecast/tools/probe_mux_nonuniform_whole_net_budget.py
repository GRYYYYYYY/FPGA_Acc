"""Retrospective one-connection budget probe; not full NET allocation or reroute."""
import json
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];result=ROOT/'experiments/mux_quadratic_history_online_loop_2026-10-06/w8_m1/result.json';cert=ROOT/'experiments/mux_quadratic_repair_detours_2026-10-06/receipt.json';verification=cert.parent/'verification.json';assert json.loads(verification.read_text())['receipt_sha256']==sha(cert)
d=json.loads(result.read_text());spec=d['allocations'][d['attempts'][0]['allocation_index']];a=json.loads((ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w8_m1.json').read_text());tgfile=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w8_timing_graph.json';mf=ROOT/'experiments/mux_full_timing_rr_2026-10-06/w8.json';assert sha(tgfile)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgfile.read_text());mapping=json.loads(mf.read_text());incoming={int(n):[] for n in tg['nodes']}
for eid,e in tg['edges'].items():
 if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
def evaluate(b):
 @lru_cache(None)
 def arrival(n):return max([F(0)]+[arrival(u)+(b[str(a['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9) for u,eid in incoming[n]])
 return max(arrival(int(n)) for n,kind in tg['nodes'].items() if kind=='SINK')
from persistent_rc_context import PersistentRCContext
from online_conflict_core import shortest_delay
p=json.loads((result.parent.parent/'protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(8,1));ctx=PersistentRCContext(case['target']);b={k:F(v) for k,v in spec['budgets_ns'].items()};rows=[]
for net in [46,143]:
 trial=dict(b);cache={};connections=[];supported=True
 for q in ctx.context[5]:
  if q['net_id']!=net:continue
  if q['source'] not in cache:cache[q['source']]=shortest_delay(ctx,q['source'],q['sink'],{4937})
  minimum=cache[q['source']]['distances'].get(q['sink'])
  if minimum is None:supported=False;continue
  cid=str(q['connection_id']);trial[cid]=max(trial[cid],F(minimum*10**9,ctx.rc.scale));connections.append(dict(connection_id=int(cid),minimum=minimum,old_budget_ns=str(b[cid]),probe_budget_ns=str(trial[cid])))
 cpd=evaluate(trial);rows.append(dict(net=net,connections=connections,supported=supported,within_cap=all(F(r['probe_budget_ns'])<=1 for r in connections),within_model_target=cpd<=F(a['target_cpd_ns']),model_cpd_ns=str(cpd),budgets_ns={k:str(v) for k,v in trial.items()},certificates={str(k):v for k,v in cache.items()}))
(cert.parent/'nonuniform_whole_net_probe.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),result_sha256=sha(result),rows=rows,scope='Retrospective firstattempt two separate wholeNET avoid4937 floor raises while preserving all other allocated budgets. Solver certificates archived but require independent checking; no actual reroute/globalcapacity/nativeSTA success.'),indent=2)+'\n');print([(r['net'],r['supported'],r['within_cap'],r['within_model_target']) for r in rows])
