"""Actual serial fixed-placement conversion-to-canonical workflow, no archived estimates."""
import sys,json,time,os,subprocess,shutil,re,ast
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha,extract
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
from serialize_whole_net_subset_v1 import serialize_subset
from rr_graph import read_rr_graph
from canonical_reload_identity_only_v2 import canonical_reload,binary,identity
from stream_native_route_audit import audit
from audit_native_route import NET
out=R/'experiments/aes_mapped_full_workflow_v1_2026-10-08';out.mkdir()
oldroot=R/'experiments/aes_rr_graph_only_v1_2026-10-08';vpr=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';shared=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';arch=shared/'vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml'
selector=R/'tools/select_resident_native_seed_subset_v1.py';tree=ast.parse(selector.read_text());loop=next(n for n in tree.body if isinstance(n,ast.For));start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec');stop=next(i for i,n in enumerate(loop.body) if i>start and isinstance(n,ast.Assert));selection=compile(ast.Module(body=loop.body[start:stop],type_ignores=[]),str(selector),'exec')
bindings={**closure([Path(__file__),selector,R/'tools/run_resident_soft_demand_wire_span_v1.py']),**{str(p):sha(p) for p in [vpr,identity,binary,arch]}}
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
from shared_compact_native_inventory_v1 import Inventory
def run(cmd,w,log,environment):
 with log.open('w') as stream:return subprocess.run(cmd,cwd=w,env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'order':['aes_cipher','aes_inv_cipher'],'scope':'Fresh original packed NET/place/RR extraction, resident fresh floors + two feedback rounds, frozen wholeNET selector AST and single compact XML inventory shared with native serialization/canonical, identity/serialization, seeded native ALL NET routing, independent endpoint/capacity audit, canonical original VPR reload. One continuous per-case wall includes all these stages and input/output hashing before timer close. Upstream pack/place/RR generation and compilation excluded. No archived floor/sketch input. All outcomes retained.'},indent=2)+'\n')
estimate=R/'experiments/aes_frozen_estimates_v1_2026-10-08'
for name in ['aes_cipher','aes_inv_cipher']:
 for file,key in [('initial_physical_verification.json','all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'),('sketch_physical_verification.json','all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'),('verification.json','complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass')]:
  path=estimate/name/'resident'/file;proof=json.loads(path.read_text());assert proof[key];assert all(sha(k)==v for k,v in proof['bindings'].items());bindings[str(path)]=sha(path)
(out/'admission_protocol.json').write_text(json.dumps({'bindings':bindings,'scope':'Both frozen AES-derived mapped candidates, all prelabel model/frame/event audits required. Original HDL semantic relation remains unproven; no validated-original-AES or completed unseen-family claim. Fresh complete workflow, staticspan50ps/tworounds/original budgets/wholeNET rank, width128 seed1 worker1 max100 timeout120 perstage. All native outcomes retained.'},indent=2)+'\n')
rows=[]
for name in ['aes_cipher','aes_inv_cipher']:
 begin=time.perf_counter();w=out/name;w.mkdir();row={'name':name,'status':'FAILED','stages':{}}
 try:
  old=json.loads((oldroot/name/'endpoints.json').read_text());bindings.update({p['path']:p['sha256'] for p in old['inputs'].values()});tick=time.perf_counter();ep,mapping=extract(*(Path(old['inputs'][k]['path']) for k in ['net','place','graph']));assert ep['connections']==old['connections'];epfile=w/'endpoints.json';epfile.write_text(json.dumps(ep)+'\n');(w/'mapping.json').write_text(json.dumps(mapping)+'\n');row['stages']['conversion']=time.perf_counter()-tick
  tick=time.perf_counter();assert run([sys.executable,str(R/'tools/run_resident_soft_demand_wire_span_v1.py'),str(epfile),str(w/'resident')],R,w/'resident.log',env)==0;row['stages']['resident']=time.perf_counter()-tick
  tick=time.perf_counter();c=json.loads((w/'resident/sketch.json').read_text());graph=Path(ep['inputs']['graph']['path']);xml=Inventory(graph);xml.validate(graph,ep['graph_sha256']);groups=defaultdict(list);scope={'c':c,'ep':ep,'xml':xml,'groups':groups,'Counter':Counter};exec(selection,scope);records=scope['records'];pending=scope['pending'];assert len(records)+len(pending)==len(ep['connections']);subset={'records':records};(w/'subset.json').write_text(json.dumps({'records':records,'pending':pending})+'\n');row['stages']['selection']=time.perf_counter()-tick
  tick=time.perf_counter()
  for f,path in [('design.blif',oldroot/name/'design.blif'),('design.net',Path(ep['inputs']['net']['path'])),('design.place',Path(ep['inputs']['place']['path']))]:bindings[str(path)]=sha(path);shutil.copyfile(path,w/f)
  cmd=[str(vpr),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full'];icmd=cmd.copy();icmd[0]=str(identity);icmd[icmd.index('--route')]='--analysis';icmd[icmd.index('--route_file')+1]='missing.route';table=w/'identity.jsonl';assert run(icmd,w,w/'identity.log',{**env,'ROUTECAST_IDENTITY_ONLY':'1','ROUTECAST_NET_IDENTITY_FILE':str(table)})==1
  inventory=xml;text,pins=serialize_subset(subset,epfile,table,w/'design.place',inventory);seed=w/'seed.route';seed.write_text(text);(w/'bindings.json').write_text(json.dumps(pins)+'\n');row['stages']['identity_serialization']=time.perf_counter()-tick
  tick=time.perf_counter();assert run(cmd,w,w/'native.log',{**env,'ROUTECAST_NATIVE_SEED':str(seed)})==0;row['stages']['native']=time.perf_counter()-tick;log=(w/'native.log').read_text();assert 'NET-aware seed imported' in log and 'VPR succeeded' in log
  cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);wire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);tick=time.perf_counter();a=audit(graph,w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert required==observed and a['overflow_units']==0;(w/'audit.json').write_text(json.dumps(a)+'\n');row['stages']['audit']=time.perf_counter()-tick
  tick=time.perf_counter();p={'files':{str(f):sha(f) for f in w.iterdir() if f.is_file()},'command':cmd,'width':128,'decision':'R','cpd_ns':cpd};result=canonical_reload(p,w,out/(name+'_canonical'),inventory);row['stages']['canonical']=time.perf_counter()-tick;row.update(status='COMPLETE_WORKFLOW_CANONICAL_PASS',cpd_ns=cpd,wirelength=wire,canonical=result,required_connections=len(ep['connections']),retained_connections=len(records))
 except Exception as error:row['error']=repr(error)
 row['files']={str(p):sha(p) for p in w.rglob('*') if p.is_file()};row['actual_complete_workflow_seconds']=time.perf_counter()-begin;rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,row['status'],row['actual_complete_workflow_seconds'],row.get('error'),flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n');assert all(r['status']=='COMPLETE_WORKFLOW_CANONICAL_PASS' for r in rows)
