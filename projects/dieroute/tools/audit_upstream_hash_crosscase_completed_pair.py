"""Review a completed cross-case pair; preserve the full five-pair denominator."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from audit_upstream_hash_native_pairs import compare
R=Path(__file__).resolve().parents[1]
D=R/'work/upstream_hash_crosscase_pairs_20261018'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',choices=['diffeq','alu4']);p.add_argument('pair',type=int,choices=range(5));a=p.parse_args();protocol=json.loads((D/'protocol.json').read_text());m=json.loads((D/'manifest.json').read_text());refs={}
 def sha(path):
  path=Path(path);h=hashlib.sha256(path.read_bytes()).hexdigest();refs[str(path)]=h;return h
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 steps=[v for v in m['steps'] if v['case']==a.case and v['pair']==a.pair];assert len(steps)==2 and all(v.get('returncode')==0 for v in steps),'Pair not successfully terminal'
 reference=D/'runs'/f'{a.case}_pair0_parent';epochs=json.loads((reference/'route.json').read_text())['iterations'];checks={};reviewer=R/'work/sb3_fixed_feedback_pair_20261015/native_tools/audit_persistent_session_provenance.py'
 for arm in ['parent','candidate']:
  directory=D/'runs'/f'{a.case}_pair{a.pair}_{arm}';mp=directory/'manifest.json';run=json.loads(mp.read_text());assert run['returncode']==0 and run['requests']==epochs;sha(mp)
  checks[arm]=compare(reference,directory)
  session=directory/'session_provenance_audit.json'
  if not session.exists():
   with (directory/'session_provenance_review.log').open('x') as log:subprocess.run(['/usr/bin/python3',str(reviewer),str(D/'recipes'/a.case/arm/'pair.json'),str(directory)],stdout=log,stderr=subprocess.STDOUT,check=True)
  v=json.loads(session.read_text());assert v['epochs']==epochs;sha(session)
  for f,h in v['source_sha256'].items():assert sha(f)==h,f
 before,after=[next(v['complete_process_wall_ns'] for v in steps if v['arm']==arm) for arm in ['parent','candidate']]
 native=R/f'work/upstream_hash_{a.case}_first_pair_review_20261018/audit.json';assert native.is_file(),'First native pair review missing';sha(native)
 out=R/'work/upstream_hash_crosscase_pair_reviews_20261018'/f'{a.case}_pair{a.pair}';out.mkdir(parents=True,exist_ok=False);snapshot=out/'terminal_step_snapshot.json';snapshot.write_text(json.dumps(steps,indent=2)+'\n');sha(snapshot)
 for f in [D/'protocol.json',Path(__file__).resolve(),R/'tools/audit_upstream_hash_native_pairs.py',reviewer]:sha(f)
 report={'status':'completed_scale256_pair_outputs_and_sessions_match_first_native_validated_parent','case':a.case,'pair':a.pair,'checks':checks,'parent_complete_process_ns':before,'candidate_complete_process_ns':after,'candidate_change_percent':100*(after/before-1),'source_sha256':refs,'scope':'One completed development pair from five planned for this case; shared host, original scale256. Later outputs equal first native-validated pair, not fresh native replay. No pooling with ex5p scale1, statistical generalization, physical FPGA or adoption claim.','adopted':False,'research_complete':False}
 (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['case','pair','parent_complete_process_ns','candidate_complete_process_ns','candidate_change_percent']}))
if __name__=='__main__':main()
