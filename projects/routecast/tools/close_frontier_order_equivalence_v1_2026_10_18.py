"""Close unchanged-data candidate using explicit feedback input-value equivalence.

No new feedback/sketch/native results are emitted or timed by this certificate.
"""
import ast,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';root=E/'mmc_frontier_order_initial_v1_2026-10-18';ip=root/'independent_verification_v1.json';ind=json.loads(ip.read_text());assert ind['repair_steps_verified']==283 and ind['NETs_with_changed_order']==33;helper=R/'tools/run_native_endpoint_v2_feedback_v1_2026_10_18.py';tree=ast.parse(helper.read_text());parents={child:node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)};alias=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='seed' for t in n.targets) and isinstance(n.value,ast.Name) and n.value.id=='candidate');fields=set();serialization=[]
 for node in ast.walk(tree):
  if not isinstance(node,ast.Name) or not isinstance(node.ctx,ast.Load) or not (node.id=='seed' or node.id=='candidate' and node.lineno<=alias.lineno):continue
  p=parents[node]
  if isinstance(p,ast.Subscript) and p.value is node:
   assert isinstance(p.slice,ast.Constant) and isinstance(p.slice.value,str);fields.add(p.slice.value)
  elif node.id=='candidate' and p is alias:pass
  elif node.id=='seed' and isinstance(p,ast.Call) and (isinstance(p.func,ast.Name) and p.func.id=='dict' or isinstance(p.func,ast.Attribute) and isinstance(p.func.value,ast.Name) and p.func.value.id=='json' and p.func.attr=='dumps'):serialization.append(node.lineno)
  else:raise AssertionError(('unexpected frame escape/read',node.id,node.lineno,ast.dump(p)[:180]))
 assert fields=={'completed_connections','required_connections','independent_connection_ledger','records','ledger','epochs'};ignored={'scope','initializer_policy'};rows=[];bindings={str(p):sha(p) for p in [ip,helper,Path(__file__)]};oldsource=json.loads((E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json').read_text());oldq={q['connection_id']:q for q in oldsource['records']}
 with Cache().installed():
  for case in ['case_01','case_02','case_03']:
   folder=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}';basep=folder/'native_retained/initial.json';newp=root/case/'initial.json';a=json.loads(basep.read_text());b=json.loads(newp.read_text());assert {k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in b.items() if k not in ignored};canonical=lambda d:json.dumps({k:v for k,v in d.items() if k not in ignored},sort_keys=True,separators=(',',':')).encode();assert canonical(a)==canonical(b);assert all(a[k]==b[k] for k in fields)
   for name in ['floors.json','history.json']:assert sha(folder/'native_retained'/name)==sha(root/case/name)
   warm_p=folder/'native_retained/verification.json';warm=json.loads(warm_p.read_text());endpoint=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';assert Path(warm['endpoint'])==endpoint and warm['schema']=='NATIVE_ENDPOINT_ANCHORED_WARM_INPUT_V2' and warm['zero_initial_history'];q={r['connection_id']:r for r in b['records']};dirty={r['net_id'] for c,r in q.items() if (r['source'],r['sink'])!=(oldq[c]['source'],oldq[c]['sink'])};assert set(warm['dirty_nets'])==dirty
   feedbackp=folder/'feedback_on/native_retained/receipt.json';feedback=json.loads(feedbackp.read_text());assert sha(helper)==feedback['bindings'][str(helper)];assert sha(basep)==feedback['bindings'][str(basep)];proto_p=feedbackp.parent/'protocol.json';proto=json.loads(proto_p.read_text());assert Path(proto['warm_seed_proof'])==warm_p and proto['rounds']==2 and proto['scheduling_policy']=='endpoint_closure_NETs_each_round'
   # Preserve all executed algorithm implementations/binaries, not only helper text.
   for p,h in feedback['bindings'].items():
    if Path(p).suffix in ['.py','.cpp','.so']:assert sha(p)==h;bindings[p]=h
   sketchp=feedbackp.parent/'sketch.json';qualityp=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}/verification.json';quality=json.loads(qualityp.read_text());assert sha(sketchp)==quality['bindings'][str(sketchp)] and quality['primary_gate_pass'] is False
   for p in [basep,newp,warm_p,endpoint,feedbackp,proto_p,sketchp,qualityp]:bindings[str(p)]=sha(p)
   rows.append(dict(case=case,feedback_frame_read_fields_equal=sorted(fields),all_nonmetadata_initial_fields_canonically_equal=True,ignored_metadata=sorted(ignored),floors_history_and_dirty_NETs_equal=True,canonical_routing_payload_sha256=hashlib.sha256(canonical(a)).hexdigest(),archived_original_cold_gate_pass=False,new_feedback_execution=False,new_native_execution=False,scope='Under the same original feedback invocation and other bound inputs, routing data/forecasts are unchanged. Exported policy labels and provenance bytes may differ; no new output bytes or runtime measurement claimed.'));print('FRONTIER ORDER FEEDBACK INPUT EQUIVALENCE PASS',case,False,flush=True)
  with (root/'feedback_input_equivalence_v1.json').open('x') as f:json.dump(dict(status='candidate_closed_identical_routing_inputs_no_prediction_change',bindings=bindings,rows=rows,frame_source_read_fields=sorted(fields),frame_passthrough_serialization_lines=serialization,reason_for_not_repeating_feedback='All algorithm-consumed initial routing values, floors, history and dirty scheduling inputs equal archived baseline. Original helper uses scope/initializer labels only by passthrough serialization, not routing reads. Repeating unchanged deterministic routing adds no prediction evidence. No fresh feedback timing, native output or original-gate pass manufactured.',remaining='Original cold/native utility, strict unseen-family, varied route failures, accepted matched full-time gain and hardware remain unmet.'),f,indent=2)
if __name__=='__main__':main()
