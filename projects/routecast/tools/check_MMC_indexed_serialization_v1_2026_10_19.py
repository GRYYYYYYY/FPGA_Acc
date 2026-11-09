"""Real full-model serialization, indexed identity lookup; compare exact baseline bytes separately."""
import pathlib,json,sys,time,hashlib
from xml.parsers import expat
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/'native_resume_prototype'))
from serialize_shared_inventory_indexed_v2 import serialize
from run_MMC_reference_incremental_astar_native_v2_2026_10_19 import Inventory,sha
R=pathlib.Path(__file__).resolve().parents[1]
def main():
 case=sys.argv[1];assert case in ['episode_01','episode_02','episode_03']
 O=R/'experiments/mmc_indexed_serialization_equivalence_v1_2026-10-19'/case;O.mkdir(parents=True,exist_ok=False)
 ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case/'demand/endpoints.json';meta=json.loads(ep.read_text());graph=pathlib.Path(meta['inputs']['graph']['path']);modelp=R/'experiments/mmc_reference_budget_incremental_astar_v2_2026-10-19'/case/'model.json';model=json.loads(modelp.read_text());assert model['eligible_for_native_serialization'] and not model['pending_connection_ids']
 needed={eid for q in model['records'] for eid in q['answer']['physical_edge_ids']};wanted=set(map(int,model['ledger']));nodes={};edges={};stack=[];nodeid=None;kind=None;eid=0;setup=time.perf_counter()
 def start(tag,a):
  nonlocal nodeid,kind,eid
  parent=stack[-1] if stack else None
  if tag=='node' and parent=='rr_nodes':nodeid=int(a['id']);kind=a['type']
  elif tag=='loc' and parent=='node' and nodeid in wanted:nodes[nodeid]=(kind,dict(a))
  elif tag=='edge' and parent=='rr_edges':
   if eid in needed:edges[eid]=tuple(int(a[k]) for k in ['src_node','sink_node','switch_id'])
   eid+=1
  stack.append(tag)
 def end(tag):
  nonlocal nodeid
  if tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes':nodeid=None
  assert stack.pop()==tag
 p=expat.ParserCreate();p.StartElementHandler=start;p.EndElementHandler=end
 with graph.open('rb') as f:p.ParseFile(f)
 assert eid==8097539 and set(nodes)==wanted and set(edges)==needed
 raw=R/'experiments/mmc_reference_incremental_astar_native_v2_2026-10-19'/case;place=raw/'design.place';identity=pathlib.Path(meta['inputs']['native_identity']['path']);assert sha(identity)==meta['inputs']['native_identity']['sha256'];setup_seconds=time.perf_counter()-setup;t=time.perf_counter();route,pins=serialize(model,ep,identity,place,Inventory(graph,meta['graph_sha256'],nodes,edges));seconds=time.perf_counter()-t;assert len(pins)==115572
 (O/'design.route').write_text(route)
 inputs=[ep,modelp,graph,identity,place,R/'tools/native_resume_prototype/serialize_shared_inventory.py',R/'tools/native_resume_prototype/serialize_shared_inventory_indexed_v2.py',pathlib.Path(__file__).resolve()]
 receipt=dict(status='INDEXED_REAL_COHORT_SERIALIZED_BASELINE_BYTE_COMPARISON_PENDING',case=case,connections=len(pins),setup_seconds=setup_seconds,serialization_seconds=seconds,route_sha256=sha(O/'design.route'),bindings={str(p):sha(p) for p in inputs},baseline_route=str(raw/'design.route'))
 (O/'receipt.json').open('x').write(json.dumps(receipt,indent=2)+'\n');print({k:v for k,v in receipt.items() if k!='bindings'},flush=True)
if __name__=='__main__':main()
