"""Review native proposal/query parity for the start-stage private variant."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_split_start_full_native_CPU_20261015';B=R/'work/native_two_phase_XRT_path_CPU_commit_20261015'
def main():
 refs={}
 def sha(f):
  key=str(f)
  if key not in refs:
   h=hashlib.sha256()
   with Path(f).open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 p=json.loads((P/'protocol.json').read_text());old=json.loads((B/'protocol.json').read_text());r=json.loads((P/'result.json').read_text())
 for doc in [p,old]:
  for f,h in doc['source_sha256'].items():assert sha(f)==h,f
 assert r['status']=='both_flags_native43_CPU_calls_and6poststates_match_gold' and len(r['steps'])==6 and all(v['returncode']==0 for v in r['steps'])
 for flag,i in [(0,2),(1,5)]:
  assert p['commands'][i]['command'][1:-1]==old['commands'][2][1:-1]
  log=P/('step'+str(i)+'.log');text=log.read_text();assert 'SHARDED_DIFFERENTIAL calls=43 isolated_owner_banks=3' in text
  data=json.loads(text.splitlines()[0]);assert data['commit_calls']==1 and data['query_calls']==42 and data['canonical_reads']==256 and data['published_nodes']==42;sha(log);sha(P/('commit'+str(flag)))
  files=list((P/('artifacts'+str(flag))).glob('*.raw'));assert len(files)==6
  for f in files:assert sha(f)==sha(Path(p['gold_directory'])/f.name),f
 for f in [P/'protocol.json',P/'result.json',B/'protocol.json',Path(__file__).resolve()]:sha(f)
 out=dict(status='split_start_both_flags_native86CPUcalls_and12poststate_files_verified',calls_per_flag=43,proposal_calls_per_flag=1,query_calls_per_flag=42,raw_files_per_flag=6,source_sha256=refs,adopted=False,research_complete=False,scope='Same frozen native authority/CSR/policy and actual priorXRTsearch7files, originalflat guarded-bank differential; bothflags1proposal42queries and sixfinalraw states. This workload does not call start; original150command fixture supplies start/error coverage. No actual XRT completion, RTL or physical result from theseCPUchecks.')
 with (P/'independent_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'])
if __name__=='__main__':main()
