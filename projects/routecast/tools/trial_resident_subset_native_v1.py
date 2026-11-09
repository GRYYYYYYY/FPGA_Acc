"""Native seed subset import and all remaining NET routing, fixed development cases."""
import sys,json,time,os,shutil,subprocess,re
from pathlib import Path
from collections import Counter
from types import MappingProxyType
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from serialize_whole_net_subset_v1 import serialize_subset
from rr_graph import read_rr_graph
from stream_native_route_audit import audit
from audit_native_route import NET
base=R/'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07';parent=R/'experiments/resident_native_seed_subset_v1_2026-10-07';vp=parent/'verification.json';proof=json.loads(vp.read_text());assert proof['wholeNET_selection_original_capacity_and_all_query_partition_pass'];out=R/'experiments/resident_subset_native_v1_2026-10-07';out.mkdir();shared=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';vpr=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';identity=R/'build/native_net_identity_only_v2_2026-10-07/routecast_net_identity_vpr';arch=shared/'vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml';bindings={**closure([Path(__file__)]),str(vp):sha(vp),**{str(p):sha(p) for p in [vpr,identity,arch]}};environment={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,order=['bigkey','dsip','misex3'],policy='Frozen complete-NET greedy capacity subset, native name/pin identity only before serialization, native seed read with true file digest check, route ALL other required NETs. seed1/worker1/width128/max100/120s process timeout. Original packedNET/place/RR. Every outcome retained, no QoR exclusion or native labels in subset rank. Native seeded search and FULL/STA then endpoint occurrence/capacity audit; canonical and fresh cold comparisons still needed. No strict proxy-budget checkpoint update from native run.'),indent=2)+'\n');rows=[]
class Inventory:
 def __init__(self,path,digest):
  self.path=path;self.digest=digest;g=read_rr_graph(path);assert g.sha256==digest;self.nodes={n:(x.type,dict(x.location)) for n,x in g.nodes.items()};self.edges=[(x.source,x.sink,x.switch_id) for x in g.edges]
 def validate(self,path,digest):assert str(path)==str(self.path) and digest==self.digest and sha(path)==digest

def run(cmd,w,log,env):
 with log.open('w') as stream:
  try:return subprocess.run(cmd,cwd=w,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
  except subprocess.TimeoutExpired:return 'TIMEOUT'
for name in ['bigkey','dsip','misex3']:
 begin=time.perf_counter();w=out/name;w.mkdir();epfile=base/name/'endpoints.json';ep=json.loads(epfile.read_text());sp=parent/name/'subset.json';assert sha(sp)==proof['bindings'][str(sp)];subset=json.loads(sp.read_text());bindings[str(sp)]=sha(sp);bindings[str(epfile)]=sha(epfile);bindings.update({x['path']:x['sha256'] for x in ep['inputs'].values()});source=R/f'experiments/mcnc_prospective_v1_2026-10-07/{name}';blif=source/'design.blif';bindings[str(blif)]=sha(blif)
 for file,path in [('design.blif',blif),('design.net',Path(ep['inputs']['net']['path'])),('design.place',Path(ep['inputs']['place']['path']))]:shutil.copyfile(path,w/file)
 graph=Path(ep['inputs']['graph']['path']);command=[str(vpr),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full'];icmd=command.copy();icmd[0]=str(identity);icmd[icmd.index('--route')]='--analysis';icmd[icmd.index('--route_file')+1]='missing.route';table=w/'identity.jsonl';icode=run(icmd,w,w/'identity.log',{**environment,'ROUTECAST_IDENTITY_ONLY':'1','ROUTECAST_NET_IDENTITY_FILE':str(table)});row=dict(name=name,identity_exit_code=icode,retained_connections=subset['retained_connections'],required_connections=subset['required_connections'],native_status='NOT_EXECUTED')
 try:
  assert icode==1 and table.exists();inventory=Inventory(graph,ep['graph_sha256']);text,pins=serialize_subset(subset,epfile,table,w/'design.place',inventory);seed=w/'seed.route';seed.write_text(text);(w/'bindings.json').write_text(json.dumps(pins)+'\n');native_tick=time.perf_counter();code=run(command,w,w/'native.log',{**environment,'ROUTECAST_NATIVE_SEED':str(seed)});row.update(native_exit_code=code,native_seconds=time.perf_counter()-native_tick,command=command)
  log=(w/'native.log').read_text();row['seed_import_logged']='NET-aware seed imported' in log;cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log);wire=re.findall(r'Total wirelength:\s*(\d+)',log);row.update(cpd_ns=float(cpd[-1]) if cpd else None,wirelength=int(wire[-1]) if wire else None)
  if code==0:
   assert row['seed_import_logged'] and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;a=audit(graph,w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};id_to_name={int(q['net_id']):ep['net_names'][str(q['net_id'])] for q in ep['connections']};expected=Counter((id_to_name[q['net_id']],q['source'],q['sink']) for q in ep['connections']);observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(id_to_name.values()));assert expected==observed and a['overflow_units']==0;row['native_status']='SEEDED_FULL_STA_ENDPOINT_CAPACITY_PASS';(w/'native_audit.json').write_text(json.dumps(a)+'\n')
  else:row['native_status']='NATIVE_FAILED_OR_TIMEOUT'
 except Exception as error:row.update(native_status='IDENTITY_SERIALIZATION_OR_AUDIT_REJECTED',error=repr(error))
 row['actual_subset_native_stage_seconds']=time.perf_counter()-begin;row['files']={str(p):sha(p) for p in w.iterdir() if p.is_file()};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('SUBSET NATIVE',row['name'],row['native_status'],row.get('cpd_ns'),row.get('error'),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All source outcomes retained. Seeded native whole routing only; canonical/cold QoR/full cost comparison pending. No proxy-budget checkpoint/heldout/net gain conclusion.'),indent=2)+'\n')
