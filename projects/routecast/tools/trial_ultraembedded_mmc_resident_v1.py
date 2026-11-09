"""Fixed pair complete model run; native labels remain prohibited pending audits."""
import json,sys,subprocess,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
src=R/'experiments/ultraembedded_mmc_native_demand_v1_2026-10-08';admission=src/'admission_review.json';a=json.loads(admission.read_text());assert a['complete_original_XML_endpoint_and_native_ignored_scope_pass'] and all(sha(k)==v for k,v in a['bindings'].items())
prereg=R/'experiments/ultraembedded_prospective_evaluation_prereg_v1_2026-10-08/protocol.json';p=json.loads(prereg.read_text());assert p['input_cases']==['usb','mmc'] and all(sha(k)==v for k,v in p['bindings'].items())
model=R/'tools/run_resident_soft_demand_affected_cache_v1.py';assert p['bindings'][str(model)]==sha(model)
out=R/'experiments/ultraembedded_mmc_resident_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__),model]),str(admission):sha(admission),str(prereg):sha(prereg)};cases=[]
for name in ['mmc']:
 proof=src/name/'verification.json';d=json.loads(proof.read_text());assert d['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'] and all(sha(k)==v for k,v in d['bindings'].items());ep=src/name/'endpoints.json';endpoint=json.loads(ep.read_text());assert all(sha(v['path'])==v['sha256'] for v in endpoint['inputs'].values());bindings[str(proof)]=sha(proof);bindings[str(ep)]=sha(ep);w=out/name;w.mkdir();cases.append(dict(name=name,required=len(endpoint['connections']),command=[sys.executable,str(model),str(ep),str(w/'resident')]))
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_per_case_seconds=1200,scope='Fixed original simultaneous wholeNET model/initial RC floors/budgets/span50ps/dynamic50ps/two rounds. Complete actual physical query scope, no native labels generated/read, all MMC outcomes retained; USB as-is rejection retained; downstream physical/event audits before cold route labels.'),indent=2)+'\n');rows=[]
for case in cases:
 w=out/case['name'];tick=time.perf_counter()
 with (w/'model.log').open('w') as log:
  try:code=subprocess.run(case['command'],cwd=R,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row=dict(name=case['name'],exit_code=code,process_seconds=time.perf_counter()-tick,required=case['required'])
 if code==0:
  c=json.loads((w/'resident/sketch.json').read_text());assert c['completed_connections']==c['required_connections']==case['required'];row.update(completed=c['completed_connections'],overflow_units=c['overflow_units'])
 row['files']={str(p):sha(p) for p in w.rglob('*') if p.is_file()};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('MODEL',case['name'],code,row.get('completed'),row.get('overflow_units'),flush=True)
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,native_labels_generated_or_read=False,scope='Estimator producer terminal only; full physical/event audit and prediction/native/HDL/timing/heldout/netgain gates remain distinct.'),indent=2)+'\n')
