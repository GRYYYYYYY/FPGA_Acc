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
b={k:F(v) for k,v in spec['budgets_ns'].items()};assert evaluate(b)==F(spec['budget_cpd_ns']);c=json.loads(cert.read_text());rows=[]
for row in c['rows']:
 cid=str(row['query']['connection_id']);trial=dict(b);trial[cid]=max(trial[cid],F(row['minimum']*10**9,c['scale']));cpd=evaluate(trial);rows.append(dict(connection_id=int(cid),old_budget_ns=str(b[cid]),probe_budget_ns=str(trial[cid]),model_cpd_ns=str(cpd),model_target_ns=a['target_cpd_ns'],within_cap=trial[cid]<=1,within_model_target=cpd<=F(a['target_cpd_ns'])))
(cert.parent/'nonuniform_budget_probe.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),result_sha256=sha(result),certificate_sha256=sha(cert),verification_sha256=sha(verification),rows=rows,scope='Retrospective perconnection independent increases, all other budgets unchanged, exact backward full old-DAG evaluation. Does not allocate whole NET avoidance, prove capacity-feasible completion/nativeSTA, or feed running main.'),indent=2)+'\n');print([(r['connection_id'],r['within_model_target']) for r in rows])
