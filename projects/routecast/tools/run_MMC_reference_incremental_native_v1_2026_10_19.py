"""Native FULL/STA only for mechanically complete registered diagnostic models."""
import pathlib,json,hashlib,shutil,subprocess,os,time,re,resource,sys
from xml.parsers import expat
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/'native_resume_prototype'))
from serialize_shared_inventory import serialize
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_reference_incremental_native_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
class Inventory:
 def __init__(self,graph,digest,nodes,edges):self.graph=graph;self.digest=digest;self.nodes=nodes;self.edges=edges
 def validate(self,graph,digest):assert pathlib.Path(graph)==self.graph and digest==self.digest and sha(self.graph)==digest

def main():
 O.mkdir(exist_ok=False);M=R/'experiments/mmc_reference_budget_incremental_v1_2026-10-19';proof=M/'independent_verification_v1.json';pv=json.loads(proof.read_text());assert pv['status']=='ALL3_ACTUAL_LAYOUT_RETAINED_AND_REBUILT_PATHS_REFERENCE_BUDGETS_TRANSACTIONS_AUDITED';plans=[];bindings={str(proof):sha(proof),str(pathlib.Path(__file__).resolve()):sha(pathlib.Path(__file__).resolve()),str(R/'tools/native_resume_prototype/serialize_shared_inventory.py'):sha(R/'tools/native_resume_prototype/serialize_shared_inventory.py')}
 for case in ['episode_01','episode_02','episode_03']:
  result=next(x for x in pv['cases'] if x['case']==case);modelp=M/case/'model.json';assert sha(modelp)==pv['bindings'][str(modelp)];I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case;ep=I/'demand/endpoints.json';assert sha(ep)==pv['bindings'][str(ep)];plans.append(dict(case=case,eligible=result['full_state_complete'],pending_CIDs=result['pending_CIDs'],model=str(modelp),endpoint=str(ep)));bindings[str(modelp)]=sha(modelp);bindings[str(ep)]=sha(ep)
 source=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/canonical/receipt.json';native=json.loads(source.read_text())['rows'][0]['canonical'];cmd0=native['command'];binary=pathlib.Path(cmd0[0]);arch=pathlib.Path(cmd0[1]);bindings[str(binary)]=sha(binary);bindings[str(arch)]=sha(arch);write(O/'protocol.json',dict(bindings=bindings,cases=plans,policy='Only complete independently audited models proceed; partial cases explicitly skipped, never scored. Serialize exact whole model via original target input-only native identity; native analysis/FULL, no rerouting. Subsequent postroute identity/canonical/trace proof remains separate.',scope='Known development actual layout updates. Reference-local budget not joint STA proof. Source constraints remain native default for QoR comparison; no original acceptance gate changed or end-to-end timing claim.'))
 outcomes=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 for plan in plans:
  case=plan['case']
  if not plan['eligible']:outcomes.append(dict(case=case,status='SKIPPED_INCOMPLETE_NOT_NATIVE_ADMISSIBLE',pending_CIDs=plan['pending_CIDs']));continue
  d=O/case;d.mkdir();ep=pathlib.Path(plan['endpoint']);meta=json.loads(ep.read_text());graph=pathlib.Path(meta['inputs']['graph']['path']);digest=meta['graph_sha256'];assert sha(graph)==digest;model=json.loads(pathlib.Path(plan['model']).read_text());assert model['eligible_for_native_serialization'] and not model['pending_connection_ids'];needed={eid for q in model['records'] for eid in q['answer']['physical_edge_ids']};wanted=set(map(int,model['ledger']));nodes={};edges={};nodeid=None;kind=None;capacity=None;stack=[];eid=0
  def start(tag,attrs):
   nonlocal nodeid,kind,capacity,eid
   parent=stack[-1] if stack else None
   if tag=='node' and parent=='rr_nodes':nodeid=int(attrs['id']);kind=attrs['type'];capacity=int(attrs['capacity'])
   if tag=='loc' and parent=='node' and nodeid in wanted:assert capacity>=model['ledger'][str(nodeid)];nodes[nodeid]=(kind,dict(attrs))
   if tag=='edge' and parent=='rr_edges':
    if eid in needed:edges[eid]=tuple(int(attrs[k]) for k in ['src_node','sink_node','switch_id'])
    eid+=1
   stack.append(tag)
  def end(tag):
   nonlocal nodeid
   if tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes':nodeid=None
   assert stack.pop()==tag
  print('SERIALIZE_INPUT_START',case,flush=True);parser=expat.ParserCreate(namespace_separator='\x1f');parser.StartElementHandler=start;parser.EndElementHandler=end
  with graph.open('rb') as f:parser.ParseFile(f)
  assert set(nodes)==wanted and set(edges)==needed and eid==8097539;I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(I/'mmc'/name,d/name)
  text,count=re.subn(r'Netlist_ID:\s*\S+','Netlist_ID: SHA256:'+sha(d/'design.net'),(d/'design.place').read_text(),count=1);assert count==1;(d/'design.place').write_text(text);identity=pathlib.Path(meta['inputs']['native_identity']['path']);assert sha(identity)==meta['inputs']['native_identity']['sha256'];route,pins=serialize(model,ep,identity,d/'design.place',Inventory(graph,digest,nodes,edges));assert len(pins)==115572;(d/'design.route').write_text(route);write(d/'serialization.json',dict(source_model=str(plan['model']),source_model_sha256=sha(pathlib.Path(plan['model'])),endpoint_sha256=sha(ep),identity=str(identity),identity_sha256=sha(identity),bound_sinks=len(pins),graph_sha256=digest,input_files={str(d/name):sha(d/name) for name in ['design.blif','design.net','design.place','design.route']}));cmd=cmd0.copy();cmd[cmd.index('--read_rr_graph')+1]=str(graph);start=time.perf_counter();print('TARGET_NATIVE_ANALYSIS_START',case,flush=True)
  def limit():resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
  with (d/'native.log').open('x') as log:code=subprocess.call(cmd,cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  text=(d/'native.log').read_text();cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text);wire=re.findall(r'Total wirelength:\s*(\d+)',text);mis=re.findall(r'Found (\d+) mismatches',text);fix=re.findall(r'Fixed (\d+) routing traces',text);row=dict(case=case,status='NATIVE_ANALYSIS_TERMINAL',command=cmd,exit_code=code,seconds=time.perf_counter()-start,full_pass='Completed routing consistency check successfully.' in text,vpr_success='VPR succeeded' in text,CPD_ns=float(cpd[-1]) if cpd else None,wirelength=int(wire[-1]) if wire else None,mismatches=int(mis[-1]) if mis else None,fixups=int(fix[-1]) if fix else None,post_packed_bytes_identical=(d/'design.net.post_routing').exists() and (d/'design.net').read_bytes()==(d/'design.net.post_routing').read_bytes(),files={str(p):sha(p) for p in d.iterdir() if p.is_file()});outcomes.append(row);write(O/'stages.json',outcomes);print({k:v for k,v in row.items() if k not in ['files','command']},flush=True)
 write(O/'receipt.json',dict(status='ALL3_MODEL_ELIGIBILITY_AND_ALLOWED_NATIVE_ANALYSES_TERMINAL',outcomes=outcomes,semantic_postroute_canonical_and_trace_audits_pending=True))
if __name__=='__main__':main()
