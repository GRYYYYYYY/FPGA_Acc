"""All outcomes retained; complete candidate native import and fresh cold comparison."""
import json,sys,os,shutil,subprocess,time,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from serialize_shared_inventory import serialize
from canonical_reload_identity_only_v2 import canonical_reload
from evaluate_priority_frozen import evaluate
base=R/'experiments/mcnc_prospective_v1_2026-10-07';parent=R/'experiments/mcnc_pending_prefix_sequence_v10_2026-10-07';out=R/'experiments/mcnc_pending_prefix_native_validation_v10_2026-10-07';out.mkdir();receipt=json.loads((parent/'receipt.json').read_text());vtr=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';vpr=vtr/'build_tileplace_vpr/vpr/vpr';arch=vtr/'vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml';identity=R/'build/native_net_identity_only_v2_2026-10-07/routecast_net_identity_vpr';kernel=R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor';inputs={str(p):sha(p) for p in (vpr,arch,identity,kernel,parent/'receipt.json')};sources=closure([Path(__file__)])
for proofname in ('verification.json','cache_cpp_v3_verification.json'):
 proof=parent/proofname;verified=json.loads(proof.read_text());assert all(sha(k)==v for k,v in verified['bindings'].items());inputs[str(proof)]=sha(proof)
for row in receipt['rows']:
 name=row['name'];ep=base/name/'endpoints.json';inputs[str(ep)]=sha(ep);inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});inputs[str(base/name/'design.blif')]=sha(base/name/'design.blif');inputs[str(parent/name/'candidate.json')]=sha(parent/name/'candidate.json')
protocol=dict(inputs=inputs,sources=sources,policy='Every case retained; only globally complete candidates serialized. Original FULL/STA analysis then post-routing NET identity normalize/original canonical FULL/STA. Fresh original VPR cold same frozen packedNET/place/RR seed1 worker1 width128 max100. No oracle fallback selection.',scope='Post-outcome development native validation. Producer total plus graph-inventory reconstruction/identity/serialization/native/canonical proof paid for complete workflow. Fresh cold routing cost reported, canonical proof and an independent graph/model/inventory reconstruction also paid on cold, matching workflow primitive construction. External accuracy/path audit excluded both, upstream pack/place/RR generation/compile excluded. Single paired run, no heldout or statistical gain claim.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};rows=[]
def run(cmd,w,log,environment):
 with log.open('w') as f:return subprocess.run(cmd,cwd=w,env=environment,stdout=f,stderr=subprocess.STDOUT,timeout=120).returncode
def native_summary(cmd,w,log,code):
 text=log.read_text();cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text);wire=re.findall(r'Total wirelength:\s*(\d+)',text)
 assert code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
 return dict(width=128,decision='R',cpd_ns=float(cpd[-1]),wirelength=int(wire[-1]),command=cmd,files={str(p):sha(p) for p in w.iterdir() if p.is_file()})
for row in receipt['rows']:
 name=row['name'];c=json.loads((parent/name/'candidate.json').read_text());result=dict(name=name,producer_stop=row['stop'],completed=c['completed_connections'],required=c['required_connections'],producer_total_seconds=row['total_seconds'],native_status='INCOMPLETE_NOT_SUBMITTED',metrics=None)
 if c['completed_connections']==c['required_connections']:
  begin=time.perf_counter();w=out/name;w.mkdir();ep=base/name/'endpoints.json';graph=base/name/'rr_graph.xml';ctx=ReusableRRFloors(ep,kernel,w/'context');inventory=SharedRRInventory(ctx);first=w/'candidate';first.mkdir()
  for f in ('design.blif','design.net','design.place'):shutil.copyfile(base/name/f,first/f)
  command=[str(vpr),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full'];icmd=command.copy();icmd[0]=str(identity);icmd[icmd.index('--route_file')+1]='missing.route';table=first/'identity.jsonl';assert run(icmd,first,first/'identity.log',{**env,'ROUTECAST_IDENTITY_ONLY':'1','ROUTECAST_NET_IDENTITY_FILE':str(table)})==1 and table.exists()
  text,pins=serialize(c,ep,table,first/'design.place',inventory);(first/'output.route').write_text(text);(first/'bindings.json').write_text(json.dumps(pins)+'\n');code=run(command,first,first/'import.log',env);summary=native_summary(command,first,first/'import.log',code);summary['command']=command.copy();summary['command'][summary['command'].index('--analysis')]='--route';canonical=canonical_reload(summary,first,w/'canonical',inventory);workflow_validation=time.perf_counter()-begin
  cold=w/'cold';cold.mkdir();tick=time.perf_counter();coldctx=ReusableRRFloors(ep,kernel,w/'cold_context');coldinventory=SharedRRInventory(coldctx)
  for f in ('design.blif','design.net','design.place'):shutil.copyfile(base/name/f,cold/f)
  cmd=command.copy();cmd[cmd.index('--analysis')]='--route';code=run(cmd,cold,cold/'run.log',env);cr=native_summary(cmd,cold,cold/'run.log',code);cc=canonical_reload(cr,cold,w/'cold_canonical',coldinventory);cold_seconds=time.perf_counter()-tick
  metrics,vectors=evaluate(graph,cold/'output.route',c);(w/'metric_vectors.json').write_text(json.dumps(vectors)+'\n');quality=summary['cpd_ns']<=cr['cpd_ns'] and summary['wirelength']<=cr['wirelength'];result.update(native_status='FULL_STA_AND_CANONICAL_SUCCESS',candidate_cpd_ns=summary['cpd_ns'],cold_cpd_ns=cr['cpd_ns'],candidate_wirelength=summary['wirelength'],cold_wirelength=cr['wirelength'],workflow_native_validation_seconds=workflow_validation,workflow_complete_seconds=row['total_seconds']+workflow_validation,cold_routing_and_canonical_seconds=cold_seconds,candidate_canonical=canonical,cold_canonical=cc,quality_pass=quality,complete_gain_pass=quality and row['total_seconds']+workflow_validation<cold_seconds,metrics=metrics,files={str(p):sha(p) for p in w.rglob('*') if p.is_file()})
 rows.append(result);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,result['native_status'],result.get('quality_pass'),result.get('candidate_cpd_ns'),result.get('cold_cpd_ns'),flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
