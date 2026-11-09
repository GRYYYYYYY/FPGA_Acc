"""Freeze SHA160 prediction before any native route label acquisition."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];F=R/'experiments/sha1_native_demand_v1_2026-10-10/sha1';ep=F/'endpoints.json';proof=F/'verification.json';v=json.loads(proof.read_text());assert v['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'] and all(sha(k)==h for k,h in v['bindings'].items())
required=len(json.loads(ep.read_text())['connections']);assert required==6273
D=R/'experiments/sha1_frozen_model_v1_2026-10-10';assert not D.exists();D.mkdir();model=D/'sha1'
scripts=['run_resident_actual_old_linear_undo_model_v13.py','run_shared_actual_old_linear_direct_lattice_audits_v4.py']
bindings={**closure([Path(__file__),*[R/'tools'/s for s in scripts]]),str(ep):sha(ep),str(proof):sha(proof)}
plan=dict(bindings=bindings,required=required,heldout_family=False,family_status='Source-local SHA160 declaration only; upstream revision and exposure/crypto overlap unresolved.',model='Unchanged actual-old linear span undo v13, full forward multi-sink/unlimited search; singleton balanced bidirectional; 2 feedback rounds/50ps price/10000 fallback states/frozen floor budgets.',metrics=dict(resource='full positive-capacity CHAN universe; normalize uniqueNET demand by capacity',spatial='same existing spatial bins/ranking/tie rules',spatial_k=20,resource_k='same existing fixed universe-fraction rule; no result-driven change',baselines=['initial_zero_price_RC','independent_connection_ledger','geometry_only'],ties='report all admissible truth cutoff tie sensitivity for fixed predicted ID ordering'),native=dict(width=128,workers=1,seed=1,max_iterations=100,check_route='full',label='final legal cold occupancy only, not transient congestion or failure training label'),scope='One new compatibility case, candidate parameters fixed before cold route labels. No new strict heldout claim. Model plus all independent physical/event audits local clock only; export/native/full workflow timer still separate required evidence.',timeout_per_stage_seconds=1200)
(D/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];tick=time.perf_counter()
for script,args,label in [(scripts[0],[str(ep),str(model)],'model'),(scripts[1],[str(model),'sha1'],'audits')]:
 t=time.perf_counter()
 with (D/(label+'.log')).open('w') as log:
  try:code=subprocess.run([sys.executable,str(R/'tools'/script),*args],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
  except subprocess.TimeoutExpired:code=124
 rows.append(dict(stage=label,exit_code=code,seconds=time.perf_counter()-t));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');assert code==0,rows[-1]
s=json.loads((model/'shared_audit_receipt.json').read_text());assert s['all_three_complete_audits_pass'] and all(sha(k)==h for k,h in s['bindings'].items())
e=json.loads((model/'verification.json').read_text());assert e['completed']==required and e['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
bindings.update(s['bindings']);bindings[str(model/'shared_audit_receipt.json')]=sha(model/'shared_audit_receipt.json');assert all(sha(k)==h for k,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,complete_candidate_physical_and_events_pass=True,completed=required,rows=rows,continuous_local_model_and_audit_seconds=time.perf_counter()-tick,scope=plan['scope']),indent=2)+'\n');print('PASS full SHA160 model and audits',required,flush=True)
