"""Validate operation-count instrumentation without interpreting it as bus traffic."""
import hashlib,json,re
from pathlib import Path
from zipfile import ZipFile
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_logical_access_profile_20261015'
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
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((P/'manifest.json').read_text());assert m['status']=='CPU_differential_complete_requires_review' and len(m['steps'])==3 and all(v['returncode']==0 for v in m['steps'])
 # Accept the historical generic runner's actual terminal spelling.
 s=(P/'source/net_commit_sharded_hbm.cpp').read_text()
 for change in reversed(json.loads((P/'instrumentation_changes.json').read_text())):assert s.count(change['after'])==1;s=s.replace(change['after'],change['before'])
 xo=R/'work/native_higher_g_hw_emu_link_20261015/commit.xo'
 with ZipFile(xo) as z:assert s.encode()==z.read('dieroute_net_commit_sharded_hbm/cpu_sources/net_commit_sharded_hbm.cpp')
 log=(P/'step2.log').read_text();rows=[{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)} for line in log.splitlines() if line.startswith('COMMIT_LOGICAL ')]
 assert len(rows)==43 and sum(v['op']==3 for v in rows)==1 and sum(v['op']==7 for v in rows)==42 and all(v['status']==0 for v in rows)
 proposal=next(v for v in rows if v['op']==3);assert proposal['used']==proposal['new_entries']==proposal['store_calls']==86 and proposal['store_key_hits']==proposal['load_key_hits']==0
 assert proposal['store_key_tests']==proposal['used']*(proposal['used']-1)//2
 assert 'SHARDED_DIFFERENTIAL calls=43 isolated_owner_banks=3' in log
 gold=R/'work/native_identity_higher_g_commit_differential_20261015';bound=json.loads((gold/'independent_audit.json').read_text());assert bound['all_net_trees_checked']==341
 for name in ['canonical_reads.raw','control.raw','nets.raw','proposal_completion.raw','resources.raw','trees.raw']:
  f=gold/'artifacts'/name;assert sha(f)==bound['source_sha256'][str(f)];assert sha(P/'artifacts'/name)==sha(f),name
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'step2.log',P/'instrumentation_changes.json',P/'commit',xo,gold/'independent_audit.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='original_full_task43call_logical_profile6poststates_match_gold',calls=rows,proposal=proposal,total_proposal_overlay_key_tests=proposal['load_key_tests']+proposal['store_key_tests'],source_sha256=refs,scope='Original full native inputs and actual XRT path; instrumentation reverses to byte-identical original packaged kernel source.43guarded flat/sharded calls and6poststates match immutable independently rebuilt341tree gold. Counts are logical C++ loop iterations, not CPU instructions, distinct memory reads, AXI transactions, HLS cycles or FPGA time. No root-cause or speedup claim.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(json.dumps(dict(status=report['status'],proposal=proposal,total_overlay_key_tests=report['total_proposal_overlay_key_tests'])))
if __name__=='__main__':main()
