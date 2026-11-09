"""Freeze completed scan timing and audited insert-boundary candidate evidence."""
from pathlib import Path
import hashlib,json,time
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 previous=R/'work/current_research_claim_matrix_v12_20261020/matrix.json'
 d=json.loads(previous.read_text())
 for name,h in d['source_sha256'].items():assert sha(R/name)==h,name
 output=R/'work/current_research_claim_matrix_v13_20261020';output.mkdir()
 plan=R/'experiments/research_plan.json';snapshot=output/'plan_snapshot.json';snapshot.write_bytes(plan.read_bytes())
 added=[
 'work/negotiate_scan_helper_routed_review_20261020/independent_audit.json',
 'work/negotiate_scan_final_timing_comparison_20261020/audit.json',
 'work/negotiate_scan_final_path_diagnosis_20261020/RTL_mapping.json',
 'work/negotiate_scan_CU_synthesis_review_20261020/audit.json',
 'work/insert_lookup_boundary_HLS_20261020/independent_RTL_audit.json',
 'work/insert_lookup_boundary_HLS_20261020/helper_boundary_review.json',
 'work/insert_lookup_boundary_HLS_20261020/caller_register_boundary_review.json',
 'work/insert_lookup_boundary_hw_20261020/compiled_XO_review.json',
 'work/insert_lookup_boundary_hw_20261020/link_protocol.json',
 'work/insert_lookup_boundary_postlink_queue_20261020/protocol.json']
 final=json.loads((R/added[0]).read_text());assert final['route']['fully_routed']==611332 and final['route']['complete'];assert final['design_timing_summary']['wns_ns']==-1.236
 rtl=json.loads((R/added[4]).read_text());assert rtl['rtl_calls']==75 and rtl['candidate_cycles']==324260 and rtl['parent_cycles']==324190
 xo=json.loads((R/added[7]).read_text());assert xo['arguments']==29 and xo['ports']==8
 for evidence in [final,rtl,xo]:
  for path,h in evidence['source_sha256'].items():assert sha(R/path)==h,path
 h2=next(c for c in d['claims'] if c['id']=='H2');h2['evidence'].extend(added);h2['measurements']=final['design_timing_summary']
 h2['limits']='Negotiation scan helper routes all611332nets but retained3.333ns setup fails:WNS-1.236ns,TNS-12223.346ns,36299endpoints. Parent-relative WNS+0.320ns and394more failures; one implementation each, no causal/statistical claim. Effective DRC severity override and external IO exceptions retained. Subsequent insert lookup candidate passes75RTL calls,324260cycles versus324190; actualXO29args8ports and exact embedded source verified. Caller capture registers present in actual compile RTL; physical link launched, final timing unproven. No adoption, adjusted-clock signoff or board result.'
 d.update(schema='dieroute.claim_matrix.v13',recorded_ns=time.time_ns(),predecessor={'path':str(previous.relative_to(R)),'sha256':sha(previous)})
 for f in added+[str(snapshot.relative_to(R)),str(Path(__file__).resolve().relative_to(R))]:d['source_sha256'][f]=sha(R/f)
 target=output/'matrix.json'
 with target.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
 p=json.loads(plan.read_text());p['current_claim_matrix']={'path':str(target.relative_to(R)),'sha256':sha(target),'status':d['status'],'research_complete':False};plan.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
 assert len(d['gates'])==8 and all(g['status']!='complete' for g in d['gates'])
 print(json.dumps({'status':d['status'],'claims':len(d['claims']),'open_gates':len(d['gates']),'sources':len(d['source_sha256']),'research_complete':False}))
if __name__=='__main__':main()
