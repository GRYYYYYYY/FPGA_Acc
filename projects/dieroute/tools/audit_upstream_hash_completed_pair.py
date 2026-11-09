"""Archive one complete pair without treating partial cohort results as final."""
import argparse,hashlib,json
from pathlib import Path
from audit_upstream_hash_native_pairs import compare
R=Path(__file__).resolve().parents[1]
D=R/'work/upstream_target_hash_native_pairs_20261018'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('pair',type=int,choices=range(5));a=p.parse_args();protocol=json.loads((D/'protocol.json').read_text());m=json.loads((D/'manifest.json').read_text());refs={}
 def sha(path):
  path=Path(path);h=hashlib.sha256(path.read_bytes()).hexdigest();refs[str(path)]=h;return h
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 steps=[s for s in m['steps'] if s['label'] in [f'pair{a.pair}_parent',f'pair{a.pair}_candidate']];assert len(steps)==2 and all(s.get('returncode')==0 for s in steps)
 checks={};reference=D/'runs/pair0_parent'
 for arm in ['parent','candidate']:
  directory=D/'runs'/f'pair{a.pair}_{arm}';manifest=directory/'manifest.json';run=json.loads(manifest.read_text());assert run['returncode']==0 and run['requests']==9;sha(manifest)
  checks[arm]=compare(reference,directory);assert len(checks[arm])==41
  for f,h in run['source_sha256'].items():assert sha(f)==h,f
 before,after=[next(s['complete_process_wall_ns'] for s in steps if s['label']==f'pair{a.pair}_{arm}') for arm in ['parent','candidate']]
 out=R/'work'/f'upstream_hash_pair{a.pair}_review_20261018';out.mkdir(exist_ok=False);snapshot=out/'terminal_step_snapshot.json';snapshot.write_text(json.dumps(steps,indent=2)+'\n');sha(snapshot)
 for f in [D/'protocol.json',Path(__file__).resolve(),R/'tools/audit_upstream_hash_native_pairs.py',R/'work/upstream_hash_first_pair_review_20261018/audit.json']:sha(f)
 result={'status':'complete_pair_outputs_match_native_validated_first_parent','pair':a.pair,'checks':checks,'parent_complete_process_ns':before,'candidate_complete_process_ns':after,'candidate_change_percent':100*(after/before-1),'source_sha256':refs,'scope':'One complete shared-host ex5p pair. Output equivalence to first native-validated pair; no repeated native validation for this pair. Incomplete five-pair cohort, unchanged baseline quality failure, not representative or FPGA performance and not adopted.','adopted':False,'research_complete':False}
 (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['pair','parent_complete_process_ns','candidate_complete_process_ns','candidate_change_percent']}))
if __name__=='__main__':main()
