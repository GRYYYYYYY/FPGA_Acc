"""Fixed minimum-cover keeper plan; original-budget hard-mask raw feasibility."""
import json,time,sys
from pathlib import Path
from types import SimpleNamespace
from array import array
from pre_route_endpoints import sha
from masked_raw_forward_v1 import Search
from MMC_zero_node_RC_shared_CSR_v1 import load
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_conflict_neighbor_avoidance_v1_2026-10-21';D.mkdir();(D/'environment_preflight.json').write_text('{"implementation":"Standard-library arrays; residual masks extend prior keeper masks; same fixed cover and budgets."}\n')
P=R/'experiments/mmc_bank_mandatory_capacity_v1_2026-10-21/verification.json';V=P.parent/'independent_verification_v1.json';plan=json.loads(P.read_text());proof=json.loads(V.read_text());assert proof['status']=='ALL3_A_B_MANDATORY_CAPACITY_AND_EXHAUSTIVE_COVER_CERTIFICATES_PASS'
B=R/'experiments/wide_cost_backend_build_v1_2026-10-13';build=json.loads((B/'build_provenance.json').read_text());assert all(sha(p)==h for p,h in build['bindings'].items());binary=B/'search.so'
bindings={str(p):sha(p) for p in [Path(__file__),P,V,B/'build_provenance.json',binary,R/'tools/masked_raw_forward_v1.py',R/'tests/test_masked_raw_forward_v1.py',R/'tools/wide_cost_search_bridge_v2.py',R/'tools/MMC_zero_node_RC_shared_CSR_v1.py']};cases=[];graph=None
for row in plan['rows']:
 ep=json.loads(Path(row['endpoint']).read_text());g=Path(ep['inputs']['graph']['path'])
 if graph is None:graph=g;graph_hash=ep['graph_sha256']
 assert graph==g and ep['graph_sha256']==graph_hash
 chosen={n for c in row['owner_conflict_components'] for n in c['cover']}
 if row['case']=='case_03':chosen.add(151)
 blocked={n:set() for n in chosen};keepers=[]
 for w in row['witnesses']:
  outside=sorted(set(w['NETs'])-chosen);assert len(outside)<=1;keeper=outside[0] if outside else min(w['NETs']);keepers.append({'node':w['node'],'keeper':keeper})
  for net in set(w['NETs'])&chosen:
   if net!=keeper:blocked[net].add(w['node'])
 bankfile=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/row['case']/'banks.jsonl'
 frozen=json.loads((R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json').read_text())
 assert sha(bankfile)==frozen['bindings'][str(bankfile)], 'Exact frozen bank binding mismatch'
 bindings[str(bankfile)]=sha(bankfile)
 mandatory=set()
 for line in bankfile.open():
  bank=json.loads(line)
  if bank['net_id'] not in chosen:mandatory.update(set(bank['A'])&set(bank['B']))
 conflict_root=R/'experiments/mmc_plus151_fixed_C_capacity_v1_2026-10-21'
 conflict_proof=conflict_root/'independent_verification_v1.json';conflict_state=conflict_root/(row['case']+'.json');unions_path=conflict_root/'C_node_unions.json'
 cv=json.loads((conflict_root/'verification.json').read_text());assert cv['files'][str(conflict_state)]==sha(conflict_state) and cv['files'][str(unions_path)]==sha(unions_path)
 unions=json.loads(unions_path.read_text())[row['case']];neighbors={n:set() for n in chosen}
 for w in json.loads(conflict_state.read_text())['hard_overloads']:
  ns={o['net_id'] for o in w['owners']};assert all(o['variant']=='C' for o in w['owners'])
  for n in ns:neighbors[n].update(ns-{n})
 for net in blocked:
  blocked[net].update(mandatory)
  for other in neighbors[net]:blocked[net].update(unions[str(other)])
 for p in [conflict_proof,conflict_state,unions_path,conflict_root/'verification.json']:bindings[str(p)]=sha(p)
 assert all(blocked.values())
 records={}
 for arm,path in row['frames'].items():
  assert plan['bindings'][path]==sha(path);bindings[path]=sha(path);frame=json.loads(Path(path).read_text());records[arm]={r['connection_id']:r for r in frame['records'] if r['net_id'] in chosen}
 assert set(records['A'])==set(records['B'])
 for cid,r in records['A'].items():assert all(r[k]==records['B'][cid][k] for k in ['net_id','source','sink','budget_integer'])
 basefile=R/'experiments/mmc_multiplacement_feedback_inputs_v1_2026-10-18'/row['case']/'base/verification.json';base=json.loads(basefile.read_text());assert base['scale']==10**18;bindings[str(basefile)]=sha(basefile)
 qs={q['connection_id']:q for q in ep['connections'] if q['net_id'] in chosen};assert set(qs)==set(records['A'])
 for cid,r in records['A'].items():assert all(r[k]==qs[cid][k] for k in ['net_id','source','sink'])
 cases.append((row['case'],blocked,keepers,records['A']));bindings[row['endpoint']]=sha(row['endpoint'])
bindings[str(graph)]=graph_hash
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'selection':'All canonical lexicographic minimum owner-conflict covers from the input-only certificate, all3 cases,37NETs including predeclared case_03 NET151 release. No best-case removal or new budgets.','residual_mask_rule':'Additionally avoid all complete original C supports of conflict neighbors, in both owner directions; preserve all A-intersection-B positive CHANNEL supports of every unextended NET. Necessary under the fixed unextended library, not sufficient for joint capacity.', 'keeper_rule':'At each mandatory capacity1 channel retain its unique noncover owner, else lowest NET ID; every other cover owner must avoid it. Fixed before any avoidance result. Failure rules out only this plan, not other covers/keeper assignments or full RR routing.','raw_cost':'Pinned zero node R/C graph, configurable buffered switches with Cinternal0; exact switch Tdel times1e18. Model original budgets require scale1e18 and identical A/B budget per CID. No timing/structural/congestion objective change claimed.','search':'Existing128bit Forward ABI, zero price/weight, per-call cap0 hard masks restored in finally. All required sinks per NET in one SSSP; shared predecessor tree exported. Dual potentials clamp unsettled nodes to maximum settled label; reachable cut exported.','certificate_scope':'Independent full original XML dual inequalities plus primal complete shared trees and original budgets; unreachable results require full cut closure. Does not prove simultaneous all-NET capacity or VPR/canonical timing legality.','native_calls':0,'scope':'Exposed fixed-bank support feasibility only; no target label reads, predictor fitting/quality or end-to-end gain.'},indent=2)+'\n')
assert sys.byteorder=='little' and all(sha(p)==h for p,h in bindings.items());start=time.perf_counter();tick=start
row,dest,cost,caps,kinds,_=load(graph);fields={'row_offsets':row,'dest_ranks':dest,'capacities':caps};rc=SimpleNamespace(increments=cost,initial=lambda n:0);search=Search(fields,rc,binary);assert len(caps)*max(cost)<2**64;setup=time.perf_counter()-tick;print('MASKED RAW SETUP',setup,flush=True)
results=[];files={}
try:
 for case,blocked,keepers,records in cases:
  for net in sorted(blocked):
   blocked[net]={n for n in blocked[net] if kinds[n] in ['CHANX','CHANY'] and caps[n]>0}
   qs=sorted([r for r in records.values() if r['net_id']==net],key=lambda r:r['connection_id']);source=qs[0]['source'];assert all(r['source']==source for r in qs);assert all(kinds[n] in ['CHANX','CHANY'] and caps[n]==1 for n in blocked[net])
   tick=time.perf_counter();answer=search.query(source,{r['sink'] for r in qs},blocked[net]);seconds=time.perf_counter()-tick
   work=D/case/f'NET_{net}';work.mkdir(parents=True)
   settled=answer['settled_bytes'];raw=array('Q');raw.frombytes(answer['raw_u128_bytes']);assert len(raw)==2*len(caps)
   assert all(raw[2*n+1]==0 for n in range(len(caps)) if settled[n])
   potentials=array('Q',(raw[2*n] if settled[n] else answer['cutoff'] for n in range(len(caps))))
   (work/'potential.u64').write_bytes(potentials.tobytes());(work/'reachable.u8').write_bytes(settled);rows=[]
   for q in qs:
    a=answer['answers'][q['sink']];out={'connection_id':q['connection_id'],'source':q['source'],'sink':q['sink'],'budget':q['budget_integer'],'reachable':a['reachable'],'minimum':a.get('minimum'),'within_budget':a['reachable'] and a['minimum']<=q['budget_integer'],'physical_edge_ids':a.get('slots')};rows.append(out)
   result={'case':case,'net_id':net,'source':source,'blocked_nodes':sorted(blocked[net]),'keepers':keepers,'cutoff':answer['cutoff'],'initial':answer['initial'],'connections':rows,'all_connections_within_budget':all(r['within_budget'] for r in rows),'search_and_copy_seconds':seconds,'potential_file':str(work/'potential.u64'),'reachable_file':str(work/'reachable.u8')};(work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
   for p in work.iterdir():files[str(p)]=sha(p)
   results.append({'case':case,'net_id':net,'connections':len(rows),'reachable':sum(r['reachable'] for r in rows),'within_budget':sum(r['within_budget'] for r in rows),'whole_NET_budget_feasible':result['all_connections_within_budget'],'search_and_copy_seconds':seconds,'result':str(work/'result.json')});print('COVER MASK',json.dumps(results[-1]),flush=True)
finally:search.close()
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps({'setup_seconds':setup,'rows':results,'total_seconds':time.perf_counter()-start,'bindings':bindings,'files':files,'scope':'Fixed keeper/mask plan only. Complete raw shortest predecessor trees when all perpin budgets pass, independently unchecked until certificate audit. No all-NET capacity, original objective, native, prediction or gain admission.'},indent=2)+'\n');print('ALL37 MASKED RAW SEARCHES TERMINAL',flush=True)
