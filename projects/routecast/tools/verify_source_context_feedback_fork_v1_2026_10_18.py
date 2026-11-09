"""Recover original predictor byte-for-byte and check real-data price range."""
import array,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha

def main():
 E=R/'experiments';out=E/'source_context_feedback_fork_contract_v1_2026-10-18';out.mkdir(exist_ok=False);p=R/'tools/run_native_endpoint_source_context_feedback_v1_2026_10_18.py';original=R/'tools/run_native_endpoint_v2_feedback_v1_2026_10_18.py';s=p.read_text();s=s.replace('\nfrom source_context_ablation_input_v1 import load as load_source_context','',1).replace(',source_context_directory=None,source_context_arm=None):','):',1);s=s.replace('\n criticalities,initial_source_history,source_context_bindings=load_source_context(endpoint,source_context_directory,source_context_arm,criticalities);bindings.update(source_context_bindings)','',1);s=s.replace("source_context_input_proof=str(Path(source_context_directory).resolve()/'verification.json'),source_context_arm=source_context_arm,source_context_history='native_accumulated_multiplier_minus1' if source_context_arm!='source_post_STA_only' else 'zero',",'',1);s=s.replace('explicit source-context initial history; addition skipped','zero initial history from previous native state; addition skipped',1).replace('Fixed source-epoch perpin criticality ordered shared-tree primary','Frozen perpin initialized criticality ordered shared-tree primary',1).replace('moved-closure floors recomputed; explicit source-context history and timing prior; fixed perpin criticality ordered shared-tree primary','moved-closure floors recomputed; zero initial history; frozen native perpin criticality ordered shared-tree primary',1);s=s.replace('prices=Counter(initial_source_history)',"prices=Counter({int(n):v for n,v in json.loads((warm_directory/'history.json').read_text()).items()})",1).replace(",'source_context_directory','source_context_arm']:parser.add_argument(name)","]:parser.add_argument(name)",1).replace(',source_context_directory=args.source_context_directory,source_context_arm=args.source_context_arm','',1);assert s==original.read_text();inputproof=E/'mmc_source_context_inputs_v1_2026-10-18/independent_verification_v1.json';v=json.loads(inputproof.read_text());assert v['status']=='all3_source_context_input_payloads_independently_verified';assert all(sha(k)==h for k,h in v['bindings'].items());hp=inputproof.parent/'source_history.json';history=json.loads(hp.read_text());assert max(history.values())==13;rows=[];bindings={str(x):sha(x) for x in [Path(__file__).resolve(),p,original,inputproof,hp,R/'tools/source_context_ablation_input_v1.py']}
 import xml.etree.ElementTree as ET
 ep=json.loads((E/'mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=sha(graph);stack=[];max_span=0
 for event,node in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(node);continue
  if node.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if node.get('type') in ['CHANX','CHANY']:
    loc=node.find('loc');max_span=max(max_span,int(loc.get('xhigh'))-int(loc.get('xlow'))+1,int(loc.get('yhigh'))-int(loc.get('ylow'))+1)
   stack[-2].remove(node);node.clear()
  if node.tag=='rr_nodes':break
  stack.pop()
 assert max_span>0
 for case in ['case_01','case_02','case_03']:
  pp=E/f'mmc_multiplacement_feedback_inputs_v1_2026-10-18/{case}/base/verification.json';b=json.loads(pp.read_text());bp=pp.parent/'node_base.u64';assert b['bindings'][str(bp)]==sha(bp);base=array.array('Q');base.frombytes(bp.read_bytes());assert len(base)==904438;groups=55300
  # One history increment at round1 is <= all NETs; present multiplicity <= NETs.
  bound=max(base)*(1+max(history.values())+groups)*(groups+1)+max_span*(b['scale']//(20*10**9));assert bound<2**64;rows.append(dict(case=case,maximum_node_base=max(base),maximum_native_initial_history=13,maximum_actual_RR_channel_span=max_span,conservative_node_price_uint64_upper_bound=bound));bindings[str(pp)]=sha(pp);bindings[str(bp)]=sha(bp)
 (out/'verification.json').write_text(json.dumps(dict(status='original_predictor_exactly_recovered_all_guards_unchanged_real_price_range_safe',bindings=bindings,original_algorithm_and_all_admission_bodies_unchanged=True,changes='Authenticated source input load; explicit initial history; provenance/descriptive metadata and CLI only.',price_range=rows,scope='Existing independent positive-history snapshot/pricing contracts reused because no price formula, search or fallback code changed. Full new arm-case physical/event audits still mandatory.'),indent=2));print('SOURCE_CONTEXT_FORK_CONTRACT_PASS',flush=True)
if __name__=='__main__':main()
