"""Review the actual migration output followed by frozen quality refinement."""
from pathlib import Path
import json,hashlib,csv
import audit_adaptive_compound_sweep_stage as sweep
import audit_compound_repeat_refresh_stage as refresh
R=Path(__file__).resolve().parents[1]
D=R/'work/native_adaptive_compound_integration_v2_20261017'
O=R/'work/native_adaptive_compound_review_20261017'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 m=json.loads((D/'manifest.json').read_text());p=json.loads((D/'protocol.json').read_text())
 assert m['status']=='adaptive_compound_terminal_requires_independent_review'
 assert len(m['stages'])==2 and all(v['status']=='terminal' for v in m['stages'])
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 parent=json.loads(Path(p['integration_parent_audit']).read_text());assert len(parent['outcomes']['adaptive'])==5
 O.mkdir(exist_ok=False);case=dict(p['cases'][0]);reviews=[]
 for name,module in [('sweep',sweep),('refresh',refresh)]:
  view=O/name;view.mkdir();protocol=dict(p);protocol['cases']=[dict(case)]
  if name=='refresh':protocol['cases'][0]['policy_parent_tree']=json.loads((D/'sweep/ex5p/manifest.json').read_text())['current_tree']
  (view/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
  (view/'launch_protocol.json').write_text(json.dumps(dict(source_sha256={}))+ '\n')
  (view/'manifest.json').write_text(json.dumps(dict(status='three_case_single_sweeps_complete_requires_independent_review'))+'\n')
  (view/'ex5p').symlink_to(D/name/'ex5p',target_is_directory=True);module.P=view;module.main();reviews.append(view/'independent_audit.json')
 def tree(p):
  return {(int(v['net_id']),int(v['child'])):(int(v['source']),int(v['parent'])) for v in csv.DictReader(Path(p).open())}
 previous=json.loads((R/'work/native_refreshed_critical_policy_v1_20261016/ex5p/manifest.json').read_text())
 result=dict(status='actual_adaptive_parent_plus_quality_refinement_reviewed',quality=m['quality'],crossings=m['crossings'],same_tree_as_serial_compound=tree(m['final_tree'])==tree(previous['current_tree']),refinement_wall_ns=m['wall_ns'],source_sha256={str(f):sha(f) for f in [D/'manifest.json',D/'protocol.json',*reviews,Path(__file__)]},scope='One actual adaptive parent and CPU refinement, not all10runs,newseed,heldout or FPGA execution. Parent routing/replay time excluded from refinement_wall_ns; no speedup implied.',research_complete=False,adopted=False)
 (O/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
