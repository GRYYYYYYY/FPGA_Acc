"""Both composed-filter flags on complete native authority and actual XRT search output."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_two_phase_filter_full_native_CPU_20261015'
def main():
 refs={}
 def sha(path):
  path=Path(path);key=str(path)
  if key not in refs:
   h=hashlib.sha256()
   with path.open('rb') as f:
    for block in iter(lambda:f.read(1048576),b''):h.update(block)
   refs[key]=h.hexdigest()
  return refs[key]
 protocol=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text())
 assert m['status']=='all_CPU_checks_terminal_requires_review' and len(m['steps'])==4 and all(v['returncode']==0 for v in m['steps'])
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 source=R/'work/native_commit_two_phase_key_filter_screen_v2_20261015/source/net_commit_sharded_hbm.cpp';restored=source.read_text()
 for c in reversed(json.loads((source.parents[1]/'changes.json').read_text())):
  assert restored.count(c['after'])==1;restored=restored.replace(c['after'],c['before'],1)
 base=R/'work/native_commit_two_phase_boundaries_20261015/source/net_commit_sharded_hbm.cpp';assert restored==base.read_text();sha(base)
 gold=R/'work/native_identity_higher_g_commit_differential_20261015';bound=json.loads((gold/'independent_audit.json').read_text());assert bound['all_net_trees_checked']==341
 names=['canonical_reads.raw','control.raw','nets.raw','proposal_completion.raw','resources.raw','trees.raw']
 for flag in [0,1]:
  log=P/f'run{flag}.log';text=log.read_text();assert 'SHARDED_DIFFERENTIAL calls=43 isolated_owner_banks=3' in text
  row=json.loads(next(v for v in text.splitlines() if v.startswith('{')))
  assert row['status']=='passed' and row['commit_calls']==1 and row['query_calls']==42 and row['canonical_reads']==256 and row['revision']==344
  for name in names:
   f=gold/'artifacts'/name;assert sha(f)==bound['source_sha256'][str(f)] and sha(P/f'artifacts{flag}'/name)==sha(f),name
  sha(log);sha(P/f'commit{flag}')
 for f in [P/'protocol.json',P/'manifest.json',gold/'independent_audit.json',source.parents[1]/'changes.json',Path(__file__).resolve()]:sha(f)
 result=dict(status='two_phase_filter_both_flags86nativecalls6poststates_match_gold',native_calls=86,flags=[0,1],poststate_files=names,prior_gold_net_trees=341,source_sha256=refs,board_result=False,research_complete=False,adopted=False,scope='Complete native authority/graph, actual XRT search output handed to separate C-model. Both flags43 guarded calls and six poststate files byte-match gold. No shared-BO XRT, RTL, timing or physical performance proof.')
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'])
if __name__=='__main__':main()
