"""Admit all six closed traces by independent ownership/count/checkpoint replay."""
import json,sys,re,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter
from concurrent.futures import ProcessPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from native_owner_trace_replay_v1 import replay
N=R/'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18'
D=R/'experiments/mmc_native_owner_trace_replay_v2_2026-10-18'
CAPS=None
COHORT_BINDINGS={}
def one(case,arm):
 out=N/case/arm;eq=out/'equivalence.json';v=json.loads(eq.read_text());row=v['row']
 assert row['status']=='MATCHED_NATIVE_FULL_BYTES_AND_INTEGER_COUNTERS_PASS'
 assert v['bindings'][str(eq)]==__import__('hashlib').sha256(b'').hexdigest()
 assert COHORT_BINDINGS[str(eq)]==sha(eq)
 normalized={**v['bindings'],str(eq):sha(eq)}
 assert all(sha(p)==h for p,h in normalized.items())
 trace=out/'owner_trace.tsv';result,state=replay(trace,CAPS,row['native_work']['rows'])
 log=(out/'native.log').read_text()
 totals=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',log)
 assert len(totals)==1
 assert tuple(sum(x[k] for x in result['iteration_stats']) for k in ['NET_operations','connection_operations','heap_pushes','heap_pops'])==tuple(map(int,totals[0]))
 epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json'
 ep=json.loads(epfile.read_text());names={ep['net_names'][str(q['net_id'])]:q['net_id'] for q in ep['connections']}
 unions={};current=None
 for line in (out/'output.route').open():
  w=line.split()
  if w and w[0]=='Net':
   current=line.split('(',1)[1].rsplit(')',1)[0] if line.rstrip().endswith(')') else None
   if current is not None:assert current in names and current not in unions;unions[current]=set()
  elif w and w[0]=='Node:':assert current in names;unions[current].add(int(w[1]))
 assert set(unions)==set(names) and len(unions)==55300
 for name,nodes in unions.items():
  value=state[names[name]];assert value[0]==0 and value[1]==1 and value[2]==0 and set(value[3])==nodes
 known=set(names.values())
 assert all(net in known or value[0] for net,value in state.items() if value[1])
 result.update(case=case,arm=arm,status='pass',all_pre_post_NET_states_and_full_checkpoints_replayed=True,final55300_physical_NET_unions_equal_matched_native_output=True,all_exact_iteration_and_aggregate_work_counters_equal=True,
               scope='Independent trace grammar, NET ownership multiplicity, checkpoints, measured native occ/cap/residual consistency, final logical NET unions and exact RouterStats. Guards are instrumented first-true observations, not independently recomputed STA/force flags or sole counterfactual causes. Unmeasured external occupancy remains unknown; no timing or forecasting benefit claim.')
 result['case_manifest_empty_self_binding_recovered_via_completed_cohort']=True
 bindings={**normalized,**closure([Path(__file__)]),str(eq):sha(eq),str(epfile):sha(epfile)}
 assert sha(trace)==bindings[str(trace)]
 proof=D/case/(arm+'.json')
 with proof.open('x') as f:json.dump(dict(bindings=bindings,**result),f,indent=2)
 print('TRACE REPLAY PASS',case,arm,result['decisions'],result['setup_attempts'],flush=True)
 return dict(case=case,arm=arm,status='pass',proof=str(proof),decisions=result['decisions'],first_true_native_guards=result['first_true_native_guards'])
def main():
 global CAPS,COHORT_BINDINGS
 cp=N/'cohort_equivalence.json';C=json.loads(cp.read_text());COHORT_BINDINGS=C['bindings'];assert C['all6_native_full_output_bytes_integer_counters_equal']
 core=R/'experiments/native_owner_trace_replay_core_v1_2026-10-18/verification.json';V=json.loads(core.read_text());assert V['status']=='pass' and len(V['positive_fixtures'])==4 and len(V['rejected_corruptions'])==11
 diagnosis=N/'self_binding_diagnosis_v1.json';assert json.loads(diagnosis.read_text())['status']=='all6_only_empty_self_entry_mismatch'
 bindings={str(diagnosis):sha(diagnosis),**C['bindings'],**V['bindings'],str(cp):sha(cp),str(core):sha(core),**closure([Path(__file__)])}
 cache=Cache()
 with cache.installed():assert all(sha(p)==h for p,h in bindings.items())
 epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256']
 CAPS=array('I');stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(CAPS);CAPS.append(int(e.get('capacity')));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 D.mkdir()
 for case in ['case_01','case_02','case_03']:(D/case).mkdir()
 with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,RR_graph_sha256=ep['graph_sha256'],cases=['case_01','case_02','case_03'],arms=['off','on'],max_processes=3,scope='Streaming replay only of existing closed observation runs; no new native run and no changing original trace files.'),f,indent=2)
 rows=[]
 with ProcessPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(one,c,a):(c,a) for c in ['case_01','case_02','case_03'] for a in ['off','on']}
  for future in as_completed(futures):
   try:rows.append(future.result())
   except Exception as e:
    import traceback
    rows.append(dict(case=futures[future][0],arm=futures[future][1],status='failed',error=repr(e),traceback=traceback.format_exc()))
   (D/'stages.json').write_text(json.dumps(rows,indent=2))
 assert len(rows)==6 and all(x['status']=='pass' for x in rows)
 for r in rows:
  p=Path(r['proof']);v=json.loads(p.read_text());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
 with cache.installed():assert all(sha(p)==h for p,h in bindings.items())
 with (D/'cohort_verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass=True,scope='Observational replay coherence on six exposed fixed native runs. First-true native guards and measured co-owners only; no independent STA/force-flag recomputation, sole counterfactual cause, estimator gain, full-flow timing or unseen-family claim.'),f,indent=2)
 print('ALL6NATIVE OWNER TRACE REPLAYS VERIFIED',flush=True)
if __name__=='__main__':main()
