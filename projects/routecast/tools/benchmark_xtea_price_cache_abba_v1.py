"""Frozen eight-run cache-only ABBA/BAAB timing with certified semantic replay."""
import json,sys,time,subprocess,resource,os,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1]
O=R/'experiments/xtea_price_cache_abba_v1_2026-10-13';O.mkdir()
refs={'A':R/'experiments/xtea_design_scoped_retained_pipeline_v1_2026-10-13','B':R/'experiments/xtea_cached_retained_pipeline_v1_2026-10-13'}
scripts={'A':R/'tools/run_design_scoped_retained_tree_v1.py','B':R/'tools/run_design_scoped_cached_retained_tree_v1.py'}
ep=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';base=R/'experiments/xtea_retained_node_base_v1_2026-10-13/verification.json';crit=R/'experiments/xtea_retained_native_inputs_v1_2026-10-13/criticality'
bindings=closure([Path(__file__),*scripts.values()]);receipts={}
for arm,d in refs.items():
 assert json.loads((d/'pipeline_terminal.json').read_text())['all_stages_completed']
 for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  p=d/'model'/name;v=json.loads(p.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
 p=d/'model/receipt.json';receipts[arm]=json.loads(p.read_text());bindings[str(p)]=sha(p)
 for p,h in receipts[arm]['files'].items():assert sha(p)==h;bindings[p]=h
order=list('ABBABAAB')
protocol=dict(bindings=bindings,order=order,arms={'A':'retained_uncached','B':'retained_ticket_cached'},runs_per_arm=4,warmup_exclusions=0,metrics=['process_wall_seconds','process_cpu_seconds','total_paid_resident_seconds','feedback_seconds','search_seconds'],verification='Every initial/floors/round0/round1/sketch byte hash equal to certified arm; every round event and non-timing record equal; frozen source/input hashes before/after experiment.',scope='Exposed fixed XTEA repeated full software-model cost only. MMC recovery concurrent; no CPU isolation or cache flushing. Input conversion/capture one-time costs and native final routing not in model timing; no FPGA/placement/heldout/end-to-end claim.',cpu_affinity_count=len(os.sched_getaffinity(0)),timeout_policy='No elapsed-time cancellation; preserve terminal evidence for every launched run.')
assert all(sha(p)==h for p,h in bindings.items());(O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for i,arm in enumerate(order):
 d=O/f'{i:02d}_{arm}';model=d/'model';d.mkdir();cmd=[sys.executable,str(scripts[arm]),str(ep),str(model),str(base),str(crit)]
 print('START',i,arm,flush=True);before=resource.getrusage(resource.RUSAGE_CHILDREN);tick=time.perf_counter()
 with (d/'model.log').open('x') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
 wall=time.perf_counter()-tick;after=resource.getrusage(resource.RUSAGE_CHILDREN);cpu=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime
 terminal=dict(exit_status=code,process_wall_seconds=wall,process_cpu_seconds=cpu);(d/'terminal.json').write_text(json.dumps(terminal)+'\n')
 if code:raise SystemExit(code)
 ref=refs[arm]/'model';r=json.loads((model/'receipt.json').read_text());expected=receipts[arm]
 assert r['bindings']==expected['bindings']
 for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:
  assert sha(model/name)==bindings[str(ref/name)]
 assert len(r['rounds'])==len(expected['rounds'])==2
 for a,b in zip(r['rounds'],expected['rounds']):
  assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
 assert all(sha(p)==h for p,h in r['files'].items())
 row=dict(index=i,arm=arm,**terminal,**{k:r[k] for k in ['total_paid_resident_seconds','feedback_seconds','search_seconds']},all_frames_and_events_equal_certified_reference=True,receipt_sha256=sha(model/'receipt.json'))
 rows.append(row);(O/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',i,arm,round(wall,3),round(cpu,3),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
summary={arm:{metric:dict(values=[r[metric] for r in rows if r['arm']==arm],median=statistics.median(r[metric] for r in rows if r['arm']==arm)) for metric in protocol['metrics']} for arm in refs}
ratios={metric:summary['B'][metric]['median']/summary['A'][metric]['median'] for metric in protocol['metrics']}
for p in O.rglob('*'):
 if p.is_file():bindings[str(p)]=sha(p)
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,summary=summary,cached_over_uncached_median_ratios=ratios,all_eight_full_model_runs_match_certified_semantics=True,scope=protocol['scope']),indent=2)+'\n')
print('BENCHMARK COMPLETE',json.dumps(ratios),flush=True)
