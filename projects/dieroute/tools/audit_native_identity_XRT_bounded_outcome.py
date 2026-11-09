"""Review bounded full-pipeline noncompletion without discarding passed search."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'work/native_identity_higher_g_xrt_pipeline_20261015'
def main():
 refs={}
 def sha(f):
  f=str(Path(f).resolve())
  if f not in refs:
   h=hashlib.sha256()
   with open(f,'rb') as v:
    for b in iter(lambda:v.read(1048576),b''):h.update(b)
   refs[f]=h.hexdigest()
  return refs[f]
 x=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert x['maximum_probe_wall_seconds']==1800 and m['status']=='bounded_diagnostic_not_completed' and m['reason']=='predeclared_diagnostic_wall_bound'
 assert 1800<=m['elapsed_wall_seconds']<1830 and m['returncode']!=0
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 assert not Path('/proc/'+str(m['child_pid'])).exists()
 descendants=[]
 for pid,birth in m['observed_descendants']:
  f=Path(f'/proc/{pid}/stat');live=f.exists() and f.read_text().split()[21]==birth and f.read_text().split()[2]!='Z';assert not live,(pid,birth);descendants.append(pid)
 assert not set(descendants)&set(x['original_jobs_untouched']);assert all(Path(f'/proc/{pid}').exists() for pid in x['original_jobs_untouched'])
 search=json.loads((P/'search_stage_audit.json').read_text());assert search['result_words'][:2]==[0,43] and len(search['byte_comparisons'])==7
 for f,h in search['source_sha256'].items():assert sha(f)==h,f
 assert not (P/'artifacts/commit').exists() and '"status":"executed"' not in (P/'stdout.log').read_text()
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'run.log',P/'stdout.log',P/'search_stage_audit.json',Path(__file__).resolve()]:sha(f)
 result=dict(status='fullgraph_XRT_search_passed_shared_BO_commit_pipeline_not_completed_within_frozen1800s',wall_bound_seconds=1800,observed_wall_seconds=m['elapsed_wall_seconds'],passed_search_artifacts=7,search_expanded=43,cancelled_new_descendant_pids=descendants,original_jobs_preserved=x['original_jobs_untouched'],source_sha256=refs,scope='Search found and raw parity retained. No completed commit/query receipt or poststate exists. Host log does not distinguish pending pre-commit setup from pending first commit; do not infer deadlock or commit correctness/failure. Only new bounded process tree stopped, no restart, budget extension, physical result or end-to-end pass.',board_result=False,research_complete=False)
 with (P/'bounded_outcome_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'])
if __name__=='__main__':main()
