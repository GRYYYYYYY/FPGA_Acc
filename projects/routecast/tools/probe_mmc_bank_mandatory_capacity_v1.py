"""Input-only supplied A/B bank infeasibility and necessary support-departure bounds."""
import json,itertools,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from bank_mandatory_cover_v1 import minimum_cover,components
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_bank_mandatory_capacity_v1_2026-10-21';D.mkdir()
G=R/'experiments/mmc_geometry_pool_forecasts_v1_2026-10-18/groups.json';geo=json.loads(G.read_text());caps={n:c for g in geo['groups'] for n,c in g['members']};assert len(caps)==258720 and set(caps.values())=={1}
IP=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';inputs=json.loads(IP.read_text());items={x['case']:x for x in inputs['cases']};BP=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json';bankplan=json.loads(BP.read_text())
bindings={str(p):sha(p) for p in [Path(__file__),G,IP,BP,R/'tools/bank_mandatory_cover_v1.py',R/'tests/test_bank_mandatory_cover_v1.py']}
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'cases':['case_01','case_02','case_03'],'selection':'All three supplied A/B libraries; no target native label is read. Mandatory support is intersection(A_NET,B_NET). Count each distinct NET once per resource.','preflight_already_observed':'Input-only inspection found8/14/29 mandatory overload channels before this receipt; this is an audit, not a prospective predictor test.','bounds':'Capacity1 common owners induce conflict cliques. Exact minimum vertex cover per connected owner component is a necessary count of NETs requiring new support. It does not guarantee successful rerouting or minimal actual repair.','exact_state_budget_per_component':100000,'independent_verifier_requirement':'Rebuild every claimed mandatory owner from all original physical connection paths in both A/B source frames and original RR edge ordinals; independently enumerate component covers when <=24vertices.','scope':'Bank feasibility/representability only, not RR/timing/native infeasibility, prediction, learning or gain. No likelihood/marginal predictor launched.','native_calls':0},indent=2)+'\n')
rows=[];start=time.perf_counter()
for case in ['case_01','case_02','case_03']:
 bp=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/case/'banks.jsonl';assert bankplan['bindings'][str(bp)]==sha(bp);bindings[str(bp)]=sha(bp);mandatory=defaultdict(list)
 for row in map(json.loads,bp.open()):
  for n in set(row['A'])&set(row['B'])&caps.keys():mandatory[n].append(row['net_id'])
 bad={n:sorted(set(owners)) for n,owners in mandatory.items() if len(set(owners))>caps[n]};edges=set()
 for owners in bad.values():edges.update(itertools.combinations(owners,2))
 parts=[]
 for nets,es in components(edges):parts.append({'NETs':nets,'edges':[list(e) for e in es],**minimum_cover(es)})
 frame_inputs={}
 for arm,key in [('A','candidate_A'),('B','candidate_B')]:
  f=Path(items[case][key]);assert inputs['bindings'][str(f)]==sha(f);bindings[str(f)]=sha(f);frame_inputs[arm]=str(f)
 ep=Path(items[case]['endpoint']);bindings[str(ep)]=sha(ep)
 rows.append({'case':case,'mandatory_overload_channels':len(bad),'mandatory_NETs':len({x for owners in bad.values() for x in owners}),'overflow_units_lower_bound':sum(len(owners)-caps[n] for n,owners in bad.items()),'witnesses':[{'node':n,'capacity':caps[n],'NETs':owners} for n,owners in sorted(bad.items())],'owner_conflict_components':parts,'necessary_new_support_NETs_lower_bound':sum(p['minimum_departures'] for p in parts),'largest_owner_component':max((len(p['NETs']) for p in parts),default=0),'endpoint':str(ep),'frames':frame_inputs})
 print('MANDATORY CAPACITY',case,len(bad),'new-support NET lower bound',rows[-1]['necessary_new_support_NETs_lower_bound'],flush=True)
assert all(sha(p)==h for p,h in bindings.items());assert all(r['mandatory_overload_channels']>0 for r in rows)
(D/'verification.json').write_text(json.dumps({'rows':rows,'seconds':time.perf_counter()-start,'bindings':bindings,'scope':'No assignment of these complete A/B trees is globally positive-CHANNEL-capacity legal. Lower bounds concern departures from supplied alternatives, not complete RR search or timing feasibility. Original prediction domains and capacity exclusions remain unchanged.'},indent=2)+'\n')
