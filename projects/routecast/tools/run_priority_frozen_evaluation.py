"""Freeze source-complete local evaluation before any priority native labels."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
from pre_route_endpoints import sha,extract
from freeze_priority_family import closure
from predict_priority_frozen import predict
from evaluate_priority_frozen import evaluate
from stream_native_route_audit import audit
from audit_native_route import NET
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
ROOT=Path(__file__).resolve().parents[1];front=ROOT/'experiments/priority_family_freeze_2026-10-07';out=ROOT/'experiments/priority_frozen_evaluation_2026-10-07';out.mkdir()
f=json.loads((front/'protocol.json').read_text());fr=json.loads((front/'receipt.json').read_text());assert fr['protocol_sha256']==sha(front/'protocol.json') and not fr['native_started'];assert all(sha(p)==d for p,d in f['sources_sha256'].items());assert all(sha(p)==d for r in fr['rows'] for p,d in r['files'].items())
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';binary=shared/'build_tileplace_vpr/vpr/vpr';arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml';sources=closure([Path(__file__)]);sources.update(f['sources_sha256']);inputs={str(x):sha(x) for x in [binary,arch,front/'protocol.json',front/'receipt.json']}
for r in fr['rows']:inputs[str(front/f"n{r['width']}/design.blif")]=sha(front/f"n{r['width']}/design.blif")
p=dict(sources=sources,inputs=inputs,cohort=f['widths'],policy=f['policy'],metrics=f['metrics'],scope='New locally generated family held out from development. Whole evaluation local source closure/native tools/config/input hashes frozen BEFORE native labels. All variants retained, no tuning. Native reference route evaluator-only; prediction takes route-free net/place/graph endpoints. Original mapped input/native pack-place-route and estimator/audit clocks separate; not accepted placement loop/netgain.')
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for width in p['cohort']:
 work=out/f'n{width}';work.mkdir();shutil.copyfile(front/f'n{width}/design.blif',work/'design.blif');cmd=[str(binary),str(arch),'design.blif','--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--write_rr_graph','rr_graph.xml','--check_route','full'];tick=time.perf_counter();timeout=False
 with (work/'native.log').open('w') as stream:
  try:code=subprocess.run(cmd,cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
  except subprocess.TimeoutExpired:code=None;timeout=True
 row=dict(width=width,native_exit_code=code,native_timeout=timeout,native_seconds=time.perf_counter()-tick,command=cmd)
 if code==0:
  text=(work/'native.log').read_text();assert 'VPR succeeded' in text;row.update(native_cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1],native_wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]),native_rrr=int(re.findall(r'Successfully routed after (\d+) routing iterations',text)[-1]))
  graph=work/'rr_graph.xml';route=work/'design.route';tick=time.perf_counter();ep,mapping=extract(work/'design.net',work/'design.place',graph);(work/'endpoints.json').write_text(json.dumps(ep,indent=2)+'\n');(work/'mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');physical=audit(graph,route);names={}
  for line in route.read_text().splitlines():
   m=NET.match(line)
   if m:names[int(m[1])]=m[2]
  assert Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections'])==Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);assert physical['overflow_units']==0;row['endpoint_audit_seconds']=time.perf_counter()-tick
  row['prediction']=predict(work/'endpoints.json',work/'candidate.json');c=json.loads((work/'candidate.json').read_text());tick=time.perf_counter();a=ImmutableXMLAudit(graph,c['graph_sha256']);ids,classes,switches,_=read(graph);ledger=Counter();unions=defaultdict(set);parents=defaultdict(dict);queries={q['connection_id']:q for q in ep['connections']}
  for record in c['records']:
   q=queries[record['connection_id']];assert all(record[k]==v for k,v in q.items());node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2
   for eid in record['answer']['physical_edge_ids']:
    edge=a.graph.edges[eid];assert edge.source==node and edge.sink not in used;node=edge.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],edge.switch_id);parent=(edge.source,eid);assert node not in parents[q['net_id']] or parents[q['net_id']][node]==parent;parents[q['net_id']][node]=parent
   assert node==q['sink'] and delay==F(record['answer']['delay'],c['scale']);ledger.update(used-unions[q['net_id']]);unions[q['net_id']].update(used)
  assert dict(ledger)=={int(k):v for k,v in c['ledger'].items()} and all(v<=a.caps[k] for k,v in ledger.items());row.update(paths_audited=len(c['records']),required_connections=c['required_connections'],path_audit_seconds=time.perf_counter()-tick);tick=time.perf_counter();row['metrics'],vectors=evaluate(graph,route,c);row['metric_seconds']=time.perf_counter()-tick
  if vectors is not None:(work/'vectors.json').write_text(json.dumps(vectors,indent=2)+'\n')
 else:row.update(prediction=None,metrics=None)
 row['files']={str(x):sha(x) for x in work.iterdir() if x.is_file()};rows.append(row);(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=len(rows)==3),indent=2)+'\n');print(width,code,row.get('prediction'),row.get('metrics',{}).get('spatial'),flush=True)
assert all(sha(x)==d for x,d in sources.items()) and all(sha(x)==d for x,d in inputs.items())
