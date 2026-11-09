"""Replay both frozen refinement stages for one completed reserved seed."""
import argparse,hashlib,json,time
from pathlib import Path
import audit_adaptive_compound_sweep_stage as sweep
import audit_compound_repeat_refresh_stage as refresh
R=Path(__file__).resolve().parents[1]
def main():
 a=argparse.ArgumentParser();a.add_argument('seed',type=int,choices=range(1,6));seed=a.parse_args().seed
 label=f'apex2_seed{seed}';folder=f'reserved_apex2_seed{seed}_refinement'+('_v2' if seed==3 else '')+'_20261017';D=R/'work'/folder;O=R/'work'/f'reserved_apex2_seed{seed}_refinement_review_20261017'
 raw=(D/'manifest.json').read_bytes();state=json.loads(raw);assert state['status']=='one_reserved_seed_refinement_terminal_requires_independent_review'
 assert len(state['cases'])==1 and len(state['stages'])==2 and all(x['status']=='terminal' for x in state['stages'])
 p=json.loads((D/'protocol.json').read_text());assert p['cases'][0]['label']==label
 O.mkdir(exist_ok=False);(O/'producer_snapshot.json').write_bytes(raw);start=time.monotonic_ns();reviews=[]
 for name,module in [('sweep',sweep),('refresh',refresh)]:
  view=O/name;view.mkdir();protocol=json.loads(json.dumps(p))
  if name=='refresh':protocol['cases'][0]['policy_parent_tree']=json.loads((D/'sweep'/label/'manifest.json').read_text())['current_tree']
  (view/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');(view/'launch_protocol.json').write_text(json.dumps(dict(source_sha256={}))+'\n');(view/'manifest.json').write_text(json.dumps(dict(status='three_case_single_sweeps_complete_requires_independent_review'))+'\n');(view/label).symlink_to(D/name/label,target_is_directory=True)
  module.P=view;module.main();reviews.append(view/'independent_audit.json')
 result=state['cases'][0];q=result['quality'];c=p['cases'][0];baseline_cross=json.loads((D/'sweep'/label/'manifest.json').read_text())['baseline_crossings']
 checks=dict(native_legal=q['legal'],wirelength_nonincrease=q['total_wirelength']<=c['baseline_wirelength'],cpd_nonincrease=q['critical_path_delay_ns']<=c['baseline_cpd_ns'],crossings_nonincrease=result['crossings']<=baseline_cross)
 files=[D/'protocol.json',O/'producer_snapshot.json',*reviews,Path(__file__),Path(sweep.__file__),Path(refresh.__file__)]
 report=dict(status='one_reserved_seed_both_refinement_stages_independently_replayed',seed=seed,checks=checks,joint_quality_pass=all(checks.values()),quality=q,crossings=result['crossings'],refinement_wall_ns=result['wall_ns'],review_wall_ns=time.monotonic_ns()-start,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},scope='One reserved seed, complete recorded native decisions and final graph/connectivity/capacity replay. Refinement timing excludes separately archived parent and preparation. No cohort-wide or physical performance claim.',research_complete=False)
 (O/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],checks=checks,joint_quality_pass=report['joint_quality_pass'])))
if __name__=='__main__':main()
