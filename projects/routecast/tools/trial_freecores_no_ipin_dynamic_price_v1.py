"""Fixed development ablation of IPIN dynamic prices, full physical scope."""
import json,sys,subprocess,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
OUT=R/'experiments/freecores_no_ipin_dynamic_price_v1_2026-10-08';OUT.mkdir()
BASE=R/'experiments/freecores_resident_v1_2026-10-08';FRONT=R/'experiments/freecores_native_demand_v1_2026-10-08';model=R/'tools/run_resident_no_ipin_dynamic_price_v1.py';audit=R/'tools/verify_freecores_no_ipin_events_v1.py';frame=R/'tools/verify_resident_demand_frame_physical_v3.py'
bindings=closure([Path(__file__),model,audit,frame]);cases=[]
for name in ['8051','xtea']:
 ep=FRONT/name/'endpoints.json';proof=FRONT/name/'verification.json';v=json.loads(proof.read_text());assert v['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'] and all(sha(k)==h for k,h in v['bindings'].items());bp=BASE/name/'resident/verification.json';b=json.loads(bp.read_text());assert b['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and all(sha(k)==h for k,h in b['bindings'].items());bindings[str(ep)]=sha(ep);bindings[str(proof)]=sha(proof);bindings[str(bp)]=sha(bp);endpoint=json.loads(ep.read_text());bindings.update({x['path']:x['sha256'] for x in endpoint['inputs'].values()});cases.append(dict(name=name,endpoint=str(ep),required=len(endpoint['connections'])))
protocol=dict(bindings=bindings,cases=cases,timeout_seconds_per_stage=1200,ablation='Only remove dynamic overuse price increments for all original XML IPINs; existing baseline already includes IPIN prices. Same initial zero-price raw RC floors/1ns-or-1.5floor budgets/CHAN span prices/50ps other-node increments/two rounds/ascending affectedNET order/wholeNET transactions. Actual overuse/affected schedule still uses all resources.',scope='Already observed development pair, not prospective unseen-family evidence. Model and audits frozen before this ablation outputs; no native labels used by algorithm and no label-identified NET or resource exceptions. Preserve all outcomes. Not a fresh continuous workflow time benchmark.')
(OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for case in cases:
 name=case['name'];w=OUT/name;w.mkdir();resident=w/'resident';tick=time.perf_counter();row=dict(name=name,status='FAILED_OR_TIMEOUT',required=case['required'])
 try:
  commands=[[sys.executable,str(model),case['endpoint'],str(resident)],[sys.executable,str(frame),str(resident),'initial'],[sys.executable,str(frame),str(resident),'sketch'],[sys.executable,str(audit),str(resident),name]]
  for i,cmd in enumerate(commands):
   with (w/f'stage{i}.log').open('w') as f:code=subprocess.run(cmd,cwd=R,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=f,stderr=subprocess.STDOUT,timeout=1200).returncode
   assert code==0,(i,code);row['last_complete_stage']=i
  for filename in ['initial.json','floors.json']:
   assert json.loads((resident/filename).read_text())==json.loads((BASE/name/'resident'/filename).read_text()),filename
  c=json.loads((resident/'sketch.json').read_text());proof=json.loads((resident/'verification.json').read_text());assert c['completed_connections']==case['required']==proof['completed'];row.update(status='COMPLETE_INITIAL_FINAL_EVENT_AUDIT_PASS',overflow_units=c['overflow_units'],events=proof['events'],committed=proof['committed'],retained=proof['retained'],initial_and_floors_semantically_identical_to_baseline=True)
 except Exception as error:row['error']=repr(error)
 row['model_plus_audits_component_seconds']=time.perf_counter()-tick;row['files']={str(p):sha(p) for p in w.rglob('*') if p.is_file()};rows.append(row);(OUT/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,row['status'],row.get('overflow_units'),row.get('error'),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(OUT/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
