"""Every complete moved-layout model connection equals canonical native physical trace."""
import pathlib,json,hashlib
from xml.parsers import expat
from native_route_ledger_import_compact import physical_paths
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_reference_incremental_canonical_v2_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 rp=O/'receipt.json';canonical=json.loads(rp.read_text());assert canonical['status']=='NATIVE_CANONICAL_SEMANTIC_FULL_STA_PHYSICAL_GATE_PASS'
 for p,h in {**canonical['bindings'],**canonical['files']}.items():assert sha(pathlib.Path(p))==h
 M=R/'experiments/mmc_reference_budget_incremental_v1_2026-10-19';proof=M/'independent_verification_v1.json';pv=json.loads(proof.read_text());case=next(x for x in pv['cases'] if x['case']=='episode_01');assert case['full_state_complete'];modelp=M/'episode_01/model.json';assert sha(modelp)==pv['bindings'][str(modelp)];model=json.loads(modelp.read_text());ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json';assert sha(ep)==pv['bindings'][str(ep)];meta=json.loads(ep.read_text());graph=pathlib.Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256'];needed={eid for q in model['records'] for eid in q['answer']['physical_edge_ids']};edges={};count=0;stack=[]
 def start(tag,a):
  nonlocal count
  parent=stack[-1] if stack else None
  if tag=='edge' and parent=='rr_edges':
   if count in needed:edges[count]=tuple(int(a[k]) for k in ['src_node','sink_node','switch_id'])
   count+=1
  stack.append(tag)
 def end(tag):assert stack.pop()==tag
 p=expat.ParserCreate(namespace_separator='\x1f');p.StartElementHandler=start;p.EndElementHandler=end
 with graph.open('rb') as f:p.ParseFile(f)
 assert count==8097539 and set(edges)==needed;route=O/'canonical/design.route';actual={}
 for name,paths in physical_paths(route).items():
  for path in paths:
   key=(name,path[0][0],path[-1][0]);assert key not in actual;actual[key]=path
 expected=set();rebuilt=0;retained=0
 for q in model['records']:
  ids=q['answer']['physical_edge_ids'];u=q['source'];path=[(u,None)]
  for eid in ids:
   a,b,s=edges[eid];assert a==u;path.append((b,s));u=b
  assert u==q['sink'] and q['answer']['delay']<=q['budget_integer'];key=(meta['net_names'][str(q['net_id'])],q['source'],q['sink']);assert key not in expected;expected.add(key);assert actual[key]==tuple(path);rebuilt+=q['mode']=='REBUILT_REFERENCE_DIAGNOSTIC';retained+=q['mode']=='RETAINED_NATIVE'
 assert set(actual)==expected and len(expected)==115572 and rebuilt==53 and retained==115519;raw=R/'experiments/mmc_reference_incremental_native_v1_2026-10-19/episode_01';serialization=json.loads((raw/'serialization.json').read_text());assert sha(raw/'design.route')==serialization['input_files'][str(raw/'design.route')];assert serialization['source_model_sha256']==sha(modelp);coldp=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19/episode_01/rows.json';cold=json.loads(coldp.read_text())[0];assert canonical['CPD_ns']<=cold['diagnostic_cpd_ns']+1e-12;wire_nonreg=canonical['wirelength']<=cold['wirelength'];assert wire_nonreg;assert canonical['wirelength']==case['present_unique_NET_CHAN_span'];bindings={str(p):sha(p) for p in [rp,proof,modelp,ep,graph,route,raw/'serialization.json',raw/'design.route',coldp,pathlib.Path(__file__).resolve()]}
 with (O/'independent_model_trace_verification_v1.json').open('x') as f:json.dump(dict(status='ALL115572_MOVED_LAYOUT_MODEL_NATIVE_PATHS_AND_EPISODE01_NATIVE_QOR_MATCH',retained_connections=retained,rebuilt_connections=rebuilt,connections=len(expected),routed_NETs=55300,cold_wirelength=cold['wirelength'],candidate_wirelength=canonical['wirelength'],cold_CPD_ns=cold['diagnostic_cpd_ns'],candidate_CPD_ns=canonical['CPD_ns'],native_wire_and_CPD_nonregression=True,canonical_ignored_fixups=canonical['fixups'],original_zero_counter_gate_pass=canonical['original_zero_counter_gate_pass'],bindings=bindings,scope='Episode01 actual moved layout only, full model traces and physical/native CPD verified. Episodes02/03 incomplete and excluded; not full cohort, original predictor quality, unseen-family, timing closure or full workflow speedup.'),f,indent=2)
 print('ACTUAL PLACEMENT MODEL/NATIVE TRACE PASS',retained,rebuilt,'wire',cold['wirelength'],canonical['wirelength'],'CPD',canonical['CPD_ns'],flush=True)
if __name__=='__main__':main()
