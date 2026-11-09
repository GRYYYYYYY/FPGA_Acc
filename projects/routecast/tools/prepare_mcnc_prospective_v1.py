"""Freeze three previously unreferenced local MCNC inputs before new outcomes."""
import json,sys,shutil,subprocess,time,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha,extract
from source_binding_v2 import closure
vtr=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';bench=vtr/'vtr_flow/benchmarks/blif';binary=vtr/'build_tileplace_vpr/vpr/vpr';arch=vtr/'vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml'
out=R/'experiments/mcnc_prospective_v1_2026-10-07';out.mkdir();names=['bigkey','dsip','misex3'];paths=[bench/(n+'.blif') for n in names];records=[]
prior=sorted((R/'experiments').rglob('protocol.json'));texts=[(str(p),p.read_text(errors='replace')) for p in prior]
for name,path in zip(names,paths):
 h=sha(path);matches=[p for p,t in texts if str(path) in t or h in t or (name+'.blif') in t];assert not matches,(name,matches)
 w=out/name;w.mkdir();shutil.copyfile(path,w/'design.blif');records.append(dict(name=name,original_path=str(path),original_sha256=h,archive_sha256=sha(w/'design.blif'),prior_protocol_matches=matches))
search=R/'experiments/mux_owned_bound_cache_2026-10-06/search.so';sources=closure([Path(__file__),R/'tools/predict_priority_frozen.py',R/'tools/evaluate_priority_frozen.py'])
inputs={str(p):sha(p) for p in [binary,arch,search,search.with_suffix('.cpp'),bench/'README',*paths]}
protocol=dict(frozen_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=records,inputs=inputs,sources=sources,policy=dict(seed=1,workers=1,channel_width=128,max_router_iterations=100,timeout_per_stage_s=120,weight_ns='1/20',max_labels=10000,fallback_limit=0,whole_net_releases=4,net_order='ascending NET/CID'),evaluation=dict(k=20,spatial_bins='all positive-capacity layer,x,y,orientation,segment bins; zeros included',incomplete='null complete metrics, retain failure',reference='original VPR same fixed placement FULL/STA after candidate freeze',selection='all three named local inputs before outcomes; no QoR-based exclusion'),prior_protocols_scanned={p:sha(p) for p,t in texts},provenance=dict(local_readme='MCNC LGSynth93 collection',upstream_commit_authenticated=False,directory_revision_label_is_not_evidence=True,unseen_family_claim=False,reason='No prior direct path/hash/basename protocol matches; indirect related-family and outside-local exposure unproven. Dataset names are not whole-family split authentication.'),scope='Prospective local transfer evaluation; pre-route pack/place/RR and endpoint extraction first, frozen existing predictor next, evaluator-only labels last. No benchmark-wide held-out claim.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for row in records:
 name=row['name'];w=out/name;cmd=[str(binary),str(arch),'design.blif','--pack','--place','--write_rr_graph','rr_graph.xml','--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100'];start=time.perf_counter()
 with (w/'prepare.log').open('w') as log:
  try:code=subprocess.run(cmd,cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode;timeout=False
  except subprocess.TimeoutExpired:code=None;timeout=True
 result=dict(name=name,command=cmd,exit_code=code,timed_out=timeout,prepare_seconds=time.perf_counter()-start,connections=None,endpoint_error=None)
 if code==0:
  try:
   ep,mapping=extract(w/'design.net',w/'design.place',w/'rr_graph.xml');(w/'endpoints.json').write_text(json.dumps(ep,indent=2)+'\n');(w/'mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');result['connections']=len(ep['connections'])
  except Exception as e:result['endpoint_error']=repr(e)
 result['files']={str(p):sha(p) for p in w.iterdir() if p.is_file()};rows.append(result);(out/'preparation_rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,code,result['connections'],result['endpoint_error'],flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items())
(out/'preparation_receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,no_route_labels_generated=True),indent=2)+'\n')
