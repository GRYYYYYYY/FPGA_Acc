"""Review isolated branch-comparison boundary and full command byte differential."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_branch_check_boundary_20261015'
def main():
 refs={}
 def sha(f):
  h=hashlib.sha256(Path(f).read_bytes()).hexdigest();refs[str(f)]=h;return h
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((P/'manifest.json').read_text());assert m['status']=='CPU_differential_complete_requires_review' and len(m['steps'])==3 and all(s['returncode']==0 for s in m['steps'])
 parent=Path(json.loads((P/'protocol.json').read_text())['parent'])
 v=(P/'source/net_commit_sharded_hbm.cpp').read_text();start=v.index('bool completed_branch_matches(');end=v.index('struct Engine {',start);helper=v[start:end]
 assert '#pragma HLS INLINE off' in helper and '#pragma HLS LATENCY min=2 max=2' in helper and 'return parent==target&&depth==expected_depth&&cost==expected_cost;' in helper
 original='if(parent!=branch.w[1]||depth!=branch.w[4]||cost!=branch.w[5])e.fail(commit_bad_path);'
 replacement='if(!completed_branch_matches(parent,branch.w[1],depth,branch.w[4],cost,branch.w[5]))e.fail(commit_bad_path);'
 assert v.count(replacement)==1 and (v[:start]+v[end:]).replace(replacement,original)==(parent/'source/net_commit_sharded_hbm.cpp').read_text()
 log=(P/'step2.log').read_text();assert 'SHARDED_DIFFERENTIAL calls=75 isolated_owner_banks=3' in log and 'launches=36' in log and 'calls=39' in log
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'source/net_commit_sharded_hbm.cpp',P/'step2.log',P/'command_differential',parent/'source/net_commit_sharded_hbm.cpp',Path(__file__).resolve()]:sha(f)
 result=dict(status='exact_final_branch_compare_extraction75_CPU_byte_differentials_pass',differential_calls=75,source_sha256=refs,scope='Exact comparator extraction from frozen narrow-error parent; no value truncation, external ABI or algorithm-budget changes. CPU ignores scheduling pragmas; RTL and timing require separate evidence.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'])
if __name__=='__main__':main()
