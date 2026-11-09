"""Fixed directed one-hop physical congestion context; final labels never opened."""
import json,array,sys,time,xml.parsers.expat as expat
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/mmc_topology_context_v1_2026-10-19';out.mkdir(exist_ok=False);spec=dict(cases=['case_01','case_02','case_03'],encoding='topology_code=owner3456_code*4+flags. bit0:exists distinct RR predecessor with positive original capacity and first-iteration occupancy>capacity; bit1:same for successor. Directed original XML RR arcs, all RR types; one hop only, no radius/threshold search.',model='One fixed primary extension. Same leave-one-layout-out folds, Laplace(S+1)/(N+2), quantization1e6, same safe-domain expected-L1 NET weights and min-B closed chooser. Keep frozen owner3456 and original216 controls, original full cold gates. No branch choice, smoothing or threshold scans.',forbidden='No final native target routes/labels in feature extraction. First-iteration context is not an admitted route candidate or budget relaxation.',scope='Old exposed MMC development data only. New context extraction plus prefix~27s/case and Bbank~460s/case, A generation, shared graph and audits remain paid. No full speed or native utility/hardware claim.',byteorder=sys.byteorder)
 (out/'protocol.json').write_text(json.dumps(spec,indent=2)+'\n');owner=R/'experiments/mmc_resource_owner_context_v1_2026-10-19';op=read(owner/'receipt.json');prefix=R/'experiments/mmc_native_first_iteration_v1_2026-10-18';pp=prefix/'physical_and_budget_verification_v1.json';pv=read(pp);ip=prefix/'input_identity_verification_v1.json';iv=read(ip);assert pv['status']=='all3_first_iteration_full_XML_physical_identity_and_budget_diagnostics_complete' and iv['status']=='all3_native_capture_inputs_current_endpoint_and_native_manifest_bindings_verified';graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';assert sha(graph)=='8d13c26981fbc46df4ae4584b848863cff89f711e6f2b30f396638fd8d7db131';cp=R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32';ids=array.array('I');ids.frombytes(cp.read_bytes());bindings={str(p):sha(p) for p in [graph,cp,pp,ip,owner/'receipt.json',Path(__file__).resolve()]};ledgers=[]
 for case in spec['cases']:
  p=prefix/case/'diagnostic_sketch_v1.json';assert sha(p)==pv['bindings'][str(p)];ledgers.append({int(n):v for n,v in read(p)['ledger'].items()});bindings[str(p)]=sha(p)
 caps=array.array('I');flags=[bytearray(904438) for _ in spec['cases']];over=[];stack=[];edges=0;begin=time.perf_counter()
 def opening(tag,a):
  nonlocal edges
  parent=stack[-1] if stack else None
  if tag=='node' and parent=='rr_nodes':assert int(a['id'])==len(caps);caps.append(int(a['capacity']))
  if tag=='edge' and parent=='rr_edges':
   u,v=int(a['src_node']),int(a['sink_node']);edges+=1
   if u!=v:
    for i,mask in enumerate(over):
     if mask[u]:flags[i][v]|=1
     if mask[v]:flags[i][u]|=2
  stack.append(tag)
 def closing(tag):
  assert stack.pop()==tag
  if tag=='rr_nodes':
   assert len(caps)==904438
   for ledger in ledgers:over.append(bytearray(cap>0 and ledger.get(n,0)>cap for n,cap in enumerate(caps)))
 parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
 with graph.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):parser.Parse(chunk,False)
 parser.Parse(b'',True);assert edges==8097539 and not stack;rows=[]
 for i,case in enumerate(spec['cases']):
  p=owner/(case+'.u16');assert op['bindings'][str(p)]==sha(p);base=array.array('H');base.frombytes(p.read_bytes());assert len(base)==len(ids)==258720;codes=array.array('H',(c*4+flags[i][n] for n,c in zip(ids,base)));assert max(codes)<13824;target=out/(case+'.u16');target.write_bytes(codes.tobytes());fp=out/(case+'.all_node_flags.u8');fp.write_bytes(flags[i]);rows.append(dict(case=case,resources=len(codes),observed_categories=len(set(codes)),overused_prefix_positive_capacity_nodes=sum(over[i]),directed_flag_counts={str(k):sum(flags[i][n]==k for n in ids) for k in range(4)}));bindings.update({str(p):sha(p) for p in [p,target,fp]});print('TOPOLOGY_CONTEXT_PRODUCED',case,rows[-1],flush=True)
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='ALL3_FIXED_DIRECTED_TOPOLOGY_CONTEXTS_PRODUCED',rows=rows,edges=edges,component_seconds=time.perf_counter()-begin,bindings=bindings,target_final_labels_read=False,independent_verification_pending=True),f,indent=2)
if __name__=='__main__':main()
