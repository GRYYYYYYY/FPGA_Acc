"""Actual XRT search artifacts handed to two-phase CPU commit, not shared BO execution."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_two_phase_XRT_path_CPU_commit_20261015'
def main():
 refs={}
 def sha(f):
  f=str(Path(f).resolve())
  if f not in refs:
   h=hashlib.sha256()
   with open(f,'rb') as s:
    for b in iter(lambda:s.read(1048576),b''):h.update(b)
   refs[f]=h.hexdigest()
  return refs[f]
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((P/'manifest.json').read_text());assert m['status']=='CPU_differential_complete_requires_review' and len(m['steps'])==3 and all(v['returncode']==0 for v in m['steps'])
 log=(P/'step2.log').read_text();row=json.loads(next(v for v in log.splitlines() if v.startswith('{')));assert row['status']=='passed' and row['commit_calls']==1 and row['query_calls']==42 and row['canonical_reads']==256 and row['revision']==344
 assert 'SHARDED_DIFFERENTIAL calls=43 isolated_owner_banks=3' in log
 gold=R/'work/native_identity_higher_g_commit_differential_20261015';prior=json.loads((gold/'independent_audit.json').read_text());assert prior['all_net_trees_checked']==341
 compared=[]
 for name in ['canonical_reads.raw','control.raw','nets.raw','proposal_completion.raw','resources.raw','trees.raw']:
  f=gold/'artifacts'/name;assert sha(f)==prior['source_sha256'][str(f)];assert sha(P/'artifacts'/name)==sha(f),name;compared.append(name)
 search=R/'work/native_identity_higher_g_xrt_pipeline_20261015/search_stage_audit.json';audit=json.loads(search.read_text());assert len(audit['byte_comparisons'])==7
 for f,h in audit['source_sha256'].items():assert sha(f)==h,f
 assert sha(P/'source/net_commit_sharded_hbm.cpp')==sha(R/'work/native_commit_two_phase_boundaries_20261015/source/net_commit_sharded_hbm.cpp')
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'step2.log',P/'commit',gold/'independent_audit.json',search,Path(__file__).resolve()]:sha(f)
 result=dict(status='actual_XRT_search_path_two_phase_CPU43call_differential_and6poststates_match_gold',commit_calls=1,query_calls=42,canonical_reads=256,revision=344,compared_poststate_files=compared,prior_independently_rebuilt_net_trees=341,source_sha256=refs,scope='Actual fullgraph XRT search exported seven artifacts, then separate two-phase CPU C-model commit/query differential with guarded owner arrays. All6poststate artifacts match immutable independently audited341tree gold. This is not the still-running shared-BO XRT commit pipeline or board execution.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'])
if __name__=='__main__':main()
