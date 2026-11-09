"""Six certified native traces; conservative per-NET overflow transition bounds."""
import concurrent.futures,json,os,sys,time,xml.etree.ElementTree as ET,traceback
from pathlib import Path
from array import array
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from native_owner_overflow_trace_replay_v1 import replay
CAPS=None
ROOT=R/'experiments/mmc_native_overflow_transition_bounds_v1_2026-10-18'
OLD=R/'experiments/mmc_native_owner_trace_replay_v2_2026-10-18'
def one(case,arm):
 start=time.perf_counter();oldp=OLD/case/(arm+'.json');v=json.loads(oldp.read_text());assert v['status']=='pass';trace=R/f'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18/{case}/{arm}/owner_trace.tsv';eq=trace.parent/'equivalence.json';e=json.loads(eq.read_text());assert v['bindings'][str(trace)]==sha(trace) and v['bindings'][str(eq)]==sha(eq);actual,state=replay(trace,CAPS,e['row']['native_work']['rows']);bounds=actual.pop('native_NET_overflow_transition_bounds')
 for k,value in actual.items():assert value==v[k],(case,arm,k)
 assert sum(bounds['counts'].values())==v['setup_attempts'];all_positive=bounds['counts'].get('definitely_positive',0);after_first=sum(x.get('definitely_positive',0) for it,x in bounds['by_iteration'].items() if int(it)>1)
 output=dict(status='all_original_replay_results_equal_new_overflow_bounds_verified',case=case,arm=arm,bindings={str(oldp):sha(oldp),str(trace):sha(trace),str(eq):sha(eq)},all_original_grammar_owner_external_boundary_and_work_results_identical=True,transitions=v['setup_attempts'],definitely_positive_transitions=all_positive,definitely_positive_after_iteration1=after_first,bounds=bounds,seconds=time.perf_counter()-start,scope='Counterfactual feasibility of the same net occupancy update under a monotone overflow guard only. Not proof that native and model compare the same candidate, objective, timing, budget or state, or that removing any guard improves quality.')
 folder=ROOT/case;folder.mkdir(exist_ok=True);out=folder/(arm+'.json');out.open('x').write(json.dumps(output,indent=2)+'\n');return dict(case=case,arm=arm,proof=str(out),transitions=v['setup_attempts'],definitely_positive=all_positive,definitely_positive_after_iteration1=after_first)
def main():
 global CAPS
 ROOT.mkdir();cp=OLD/'cohort_verification.json';cohort=json.loads(cp.read_text());assert cohort['all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass'];contract=R/'experiments/native_overflow_transition_bounds_contract_v1_2026-10-18/verification.json';fork=contract.parent/'fork_recovery_v1.json';core=json.loads(contract.read_text());rec=json.loads(fork.read_text());assert core['unknown_interval_extrema_enumerated'] and rec['original_replay_exactly_recovered'];bindings={**closure([Path(__file__)]),str(cp):sha(cp),str(contract):sha(contract),str(fork):sha(fork)}
 for d in [core,rec]:
  for k,h in d['bindings'].items():assert sha(k)==h;bindings[k]=h
 seen={}
 for case in ['case_01','case_02','case_03']:
  for arm in ['off','on']:
   p=OLD/case/(arm+'.json');v=json.loads(p.read_text());assert cohort['bindings'][str(p)]==sha(p)
   for k,h in v['bindings'].items():
    if k not in seen:seen[k]=sha(k)
    assert seen[k]==h,k
   bindings[str(p)]=sha(p)
 ep=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';endpoint=json.loads(ep.read_text());graph=Path(endpoint['inputs']['graph']['path']);assert sha(graph)==endpoint['graph_sha256'];bindings[str(graph)]=sha(graph);CAPS=array('I');stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':assert int(e.get('id'))==len(CAPS);CAPS.append(int(e.get('capacity')));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(CAPS)==904438
 protocol=dict(bindings=bindings,cases=['case_01','case_02','case_03'],arms=['off','on'],maximum_workers=2,metric='delta sum_RR max(0,native_occupancy-capacity) across complete NET operation',external_policy='Use measured residual exactly within certified unchanged boundary. Absence of old-owned node in complete pre-operation overuse V list supplies only native occ<=cap. All other unknown external occupancy is nonnegative without assumed zero.',scope='Read-only conservative trajectory diagnostic. Existing routes/traces/model guards unchanged; no new native runs or estimator promotion.')
 (ROOT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(ROOT/'live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=stat[19]))+'\n');print('BOUND_REPLAY_PREFLIGHT_COMPLETE',flush=True);rows=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  fs={pool.submit(one,c,a):(c,a) for c in ['case_01','case_02','case_03'] for a in ['off','on']}
  for f in concurrent.futures.as_completed(fs):
   row=f.result();rows.append(row);(ROOT/'stages.json').write_text(json.dumps(rows,indent=2)+'\n');print('NATIVE_OVERFLOW_BOUND_REPLAY_DONE',json.dumps(row),flush=True)
 assert len(rows)==6
 for row in rows:bindings[row['proof']]=sha(row['proof'])
 result=dict(status='all6_native_NET_transition_bounds_complete_original_replay_results_identical',bindings=bindings,cases=rows,definitely_positive_transitions_total=sum(x['definitely_positive'] for x in rows),definitely_positive_after_iteration1_total=sum(x['definitely_positive_after_iteration1'] for x in rows),scope=protocol['scope'],next_action='Use actual conservative bounds as a mechanism observation only. Do not relax the original estimator guards, change budget controls or claim causal quality improvement from native behavior alone.')
 (ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
