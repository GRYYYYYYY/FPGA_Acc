"""Balanced serial full-model benchmark; not native workflow speed evidence."""
import json,sys,subprocess,time,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
name=sys.argv[1];assert name in ('8051','xtea')
mmc=R/'experiments/ultraembedded_mmc_resident_reused_heap_v2_2026-10-08/mmc'
# Require the complete large-case correctness gates before benchmarking candidate.
for file in ['parity_verification.json','initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
 proof=json.loads((mmc/file).read_text());assert all(sha(k)==h for k,h in proof['bindings'].items())
 if file=='parity_verification.json':assert proof['all_five_complete_state_files_byte_equal'] and proof['all_feedback_events_price_schedule_epoch_and_outcome_equal']
 else:assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and proof['completed']==115572
 if file=='verification.json':assert proof['events']==98479 and proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
endpoint=R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json'
baseline=R/'experiments/freecores_resident_v1_2026-10-08'/name/'resident'
runners={'baseline':R/'tools/run_resident_soft_demand_affected_cache_v1.py','candidate':R/'tools/run_resident_soft_demand_reused_heap_v2.py'}
bindings=closure([Path(__file__),*runners.values()]);bindings[str(endpoint)]=sha(endpoint)
for x in json.loads(endpoint.read_text())['inputs'].values():bindings[x['path']]=x['sha256']
for folder in ['soft_demand_workspace_build_v1_2026-10-08','soft_demand_workspace_heap_build_v2_2026-10-08']:
 p=R/'experiments'/folder/'search.so';bindings[str(p)]=sha(p)
order=[['baseline','candidate'],['candidate','baseline'],['baseline','candidate']]
out=R/'experiments/resident_reused_heap_paired_model_cost_v1_2026-10-08'/name;out.mkdir(parents=True)
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,name=name,pairs=order,timeout_seconds=1200,scope='Three balanced serial pairs, complete fixed-endpoint initial plus two feedback rounds/model export. subprocess perf_counter includes load/hash/search/serialization, excludes post-hoc parity/native/export/pre-route/full physical auditing. Not whole workflow gain or stability/generalization proof.'),indent=2)+'\n')
rows=[]
for pair,arms in enumerate(order):
 for mode in arms:
  dest=out/(str(pair)+'_'+mode);log=out/(str(pair)+'_'+mode+'.log');tick=time.perf_counter()
  try:
   with log.open('w') as f:r=subprocess.run([sys.executable,str(runners[mode]),str(endpoint),str(dest)],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
   elapsed=time.perf_counter()-tick;assert r.returncode==0
   for file in ('floors.json','initial.json','round0.json','round1.json','sketch.json'):assert (dest/file).read_bytes()==(baseline/file).read_bytes(),file
   a=json.loads((dest/'receipt.json').read_text());b=json.loads((baseline/'receipt.json').read_text());assert len(a['rounds'])==len(b['rounds'])==2
   for x,y in zip(a['rounds'],b['rounds']):
    for k in y:
     if k not in ('seconds','state_file'):assert x[k]==y[k],k
   assert all(sha(k)==h for k,h in bindings.items())
   row=dict(pair=pair,mode=mode,status='FULL_MODEL_PARITY_PASS',model_subprocess_seconds=elapsed)
  except Exception as error:
   rows.append(dict(pair=pair,mode=mode,status='FAILED_OR_TIMEOUT',error=repr(error),elapsed_to_failure_seconds=time.perf_counter()-tick));(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');raise
  rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
ratios=[]
for pair in range(3):
 d={x['mode']:x['model_subprocess_seconds'] for x in rows if x['pair']==pair};ratios.append(d['candidate']/d['baseline'])
(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,paired_ratios=ratios,median_model_ratio=statistics.median(ratios),whole_native_workflow_gain_proven=False),indent=2)+'\n')
