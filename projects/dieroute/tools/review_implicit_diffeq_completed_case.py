"""Independent one-case interim review without changing the three-case producer."""
from pathlib import Path
import hashlib,json,time
import audit_compound_repeat_sweep_stage as sweep
import audit_compound_repeat_refresh_stage as refresh
from audit_implicit_decision_equivalence_strict import signature
R=Path(__file__).resolve().parents[1];D=R/'work/native_implicit_compound_repeat_v2_20261017';B=R/'work/native_instrumented_compound_repeat_20261016';O=R/'work/implicit_diffeq_complete_review_20261017'
def main():
 start=time.monotonic_ns();raw=(D/'manifest.json').read_bytes();state=json.loads(raw);cases=[c for c in state['cases'] if c['case']=='diffeq'];assert len(cases)==1;case_result=cases[0]
 stages=[v for v in state['stages'] if v['case']=='diffeq'];assert len(stages)==7 and all(v['status']=='terminal' and v.get('returncode',0)==0 for v in stages)
 O.mkdir(exist_ok=False);(O/'producer_snapshot.json').write_bytes(raw);p=json.loads((D/'protocol.json').read_text());case=dict(p['cases'][1]);assert case['label']=='diffeq';reviews=[];comparison={};refs={}
 for name,module in [('sweep',sweep),('refresh',refresh)]:
  view=O/name;view.mkdir();protocol=dict(p);protocol['cases']=[dict(case)]
  if name=='refresh':protocol['cases'][0]['policy_parent_tree']=json.loads((D/'sweep/diffeq/manifest.json').read_text())['current_tree']
  (view/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');(view/'launch_protocol.json').write_text(json.dumps(dict(source_sha256={}))+'\n');(view/'manifest.json').write_text(json.dumps(dict(status='three_case_single_sweeps_complete_requires_independent_review'))+'\n');(view/'diffeq').symlink_to(D/name/'diffeq',target_is_directory=True)
  module.P=view;module.main();reviews.append(view/'independent_audit.json')
  left=B/name/'diffeq/manifest.json';right=D/name/'diffeq/manifest.json';a=json.loads(left.read_text());b=json.loads(right.read_text());comparison[name]=[signature(s) for s in a['steps']]==[signature(s) for s in b['steps']]
  for f in [left,right]:refs[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
 oldstate=json.loads((B/'manifest.json').read_text());old=next(c for c in oldstate['cases'] if c['case']=='diffeq');a=Path(old['final_tree']);b=Path(case_result['final_tree']);same=a.read_bytes()==b.read_bytes();quality_same=all(old['quality'][k]==case_result['quality'][k] for k in ['total_wirelength','critical_path_delay_ns']) and old['crossings']==case_result['crossings']
 for f in [D/'protocol.json',O/'producer_snapshot.json',B/'manifest.json',*reviews,a,b,Path(__file__)]:refs[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
 report=dict(status='single_diffeq_implicit_full_case_independent_replay_and_comparison_complete',decisions_identical=comparison,final_tree_identical=same,quality_identical=quality_same,quality=case_result['quality'],crossings=case_result['crossings'],candidate_full_seconds=case_result['wall_ns']/1e9,reference_full_seconds=old['wall_ns']/1e9,candidate_stages=stages,review_wall_ns=time.monotonic_ns()-start,source_sha256=refs,scope='One diffeq case only; both native decision and final graph/connectivity/capacity audits reused over isolated one-case views. Shared-host single execution and unchanged seed; time comparison not statistically controlled or FPGA speedup. Diffeq/alu4 and reserved validation pending.',research_complete=False,adopted=False)
 (O/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','quality','candidate_stages']}))
if __name__=='__main__':main()
