"""Candidate publication precedes fixed-placement original-native labels."""
import json,sys,subprocess,time,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from evaluate_priority_frozen import evaluate
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/mcnc_prospective_v1_2026-10-07';prep=json.loads((out/'preparation_receipt.json').read_text());prior=json.loads((out/'protocol.json').read_text());assert prep['protocol_sha256']==sha(out/'protocol.json');assert all(sha(p)==h for p,h in {**prior['inputs'],**prior['sources']}.items())
inputs=dict(prior['inputs']);inputs.update({str(out/'preparation_receipt.json'):sha(out/'preparation_receipt.json')});sources=closure([Path(__file__),R/'tools/predict_priority_frozen.py'])
for row in prep['rows']:
 assert row['exit_code']==0 and row['endpoint_error'] is None;inputs.update(row['files'])
protocol=dict(inputs=inputs,sources=sources,preparation_protocol_sha256=sha(out/'protocol.json'),order='bigkey,dsip,misex3; each prediction published and independently audited before evaluator-only native labels',timeout_per_process_s=120,no_retuning=True,unseen_family_claim=False,scope='Fixed frozen capacity predictor local transfer test; does not integrate predictor into native router. Prediction and native fixed-placement cost reported separately; no feedback net-gain claim.')
(out/'evaluation_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[];vpr=next(Path(p) for p in prior['inputs'] if p.endswith('/vpr/vpr'));arch=next(Path(p) for p in prior['inputs'] if p.endswith('.xml'));bindings=dict(inputs)
for row in prep['rows']:
 name=row['name'];w=out/name;candidate=w/'candidate.json';start=time.perf_counter()
 cmd=[sys.executable,'-c','import sys,json;from predict_priority_frozen import predict;print(json.dumps(predict(sys.argv[1],sys.argv[2])))',str(w/'endpoints.json'),str(candidate)];env=None
 with (w/'prediction.log').open('w') as log:
  import os
  environment=dict(os.environ,PYTHONPATH=str(R/'tools'))
  try:code=subprocess.run(cmd,cwd=w,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode;timeout=False
  except subprocess.TimeoutExpired:code=None;timeout=True
 result=dict(name=name,prediction_exit_code=code,prediction_timeout=timeout,prediction_wall_seconds=time.perf_counter()-start,candidate_sha256=sha(candidate) if candidate.exists() else None,complete_metrics=None)
 if code==0 and candidate.exists():
  c=json.loads(candidate.read_text());ep=json.loads((w/'endpoints.json').read_text());a=ImmutableXMLAudit(w/'rr_graph.xml',ep['graph_sha256']);audit=a.verify(ep,c,topology=True);(w/'candidate_audit.json').write_text(json.dumps(audit,indent=2)+'\n');result.update(status=c['status'],completed_connections=c['completed_connections'],required_connections=c['required_connections'],failure=c['failure'])
 # No prediction process ever sees a native design.route from this case.
 cmd=[str(vpr),str(arch),'design.blif','--route','--read_rr_graph','rr_graph.xml','--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full'];start=time.perf_counter()
 with (w/'native.log').open('w') as log:
  try:ncode=subprocess.run(cmd,cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode;ntimeout=False
  except subprocess.TimeoutExpired:ncode=None;ntimeout=True
 result.update(native_exit_code=ncode,native_timeout=ntimeout,native_wall_seconds=time.perf_counter()-start)
 text=(w/'native.log').read_text();cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text);wire=re.findall(r'Total wirelength:\s*(\d+)',text);result.update(native_cpd_ns=float(cpd[-1]) if cpd else None,native_wirelength=int(wire[-1]) if wire else None)
 if ncode==0 and code==0 and candidate.exists():
  assert 'Completed routing consistency check successfully.' in text and 'VPR succeeded' in text
  assert sha(candidate)==result['candidate_sha256'];metrics,vectors=evaluate(w/'rr_graph.xml',w/'design.route',c);result['complete_metrics']=metrics
  if vectors is not None:(w/'metric_vectors.json').write_text(json.dumps(vectors)+'\n')
 result['files']={str(p):sha(p) for p in w.iterdir() if p.is_file()};rows.append(result);(out/'evaluation_rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,result.get('status'),result.get('completed_connections'),ncode,metrics if 'metrics' in locals() else None,flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items())
(out/'evaluation_receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'evaluation_protocol.json'),rows=rows,scope=protocol['scope']),indent=2)+'\n')
