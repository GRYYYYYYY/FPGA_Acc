"""Check exact extraction reversal and both original75-command CPU comparisons."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_split_start_CPU_20261015'
def main():
 p=json.loads((P/'protocol.json').read_text());result=json.loads((P/'result.json').read_text());change=json.loads((P/'extraction_map.json').read_text());refs={}
 def sha(f):
  k=str(f)
  if k not in refs:refs[k]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
  return refs[k]
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 s=(P/'source/net_commit_sharded_hbm.cpp').read_text();fragment=change['original_fragment'];s=s.removeprefix(change['guard']).replace(change['helper'],'',1).replace('#if !DIEROUTE_NATIVE_SPLIT_START_PHASE\n'+fragment+'#endif\n',fragment,1).replace(change['replacement_call'],change['original_call'],1);parent=Path(change['parent']);assert s==parent.read_text() and sha(parent)==change['parent_sha256'];assert len(result['steps'])==6 and all(v['returncode']==0 for v in result['steps'])
 for flag,i in [(0,2),(1,5)]:
  log=P/('step'+str(i)+'.log');assert 'SHARDED_DIFFERENTIAL calls=75 isolated_owner_banks=3' in log.read_text();sha(log);sha(P/('command_differential'+str(flag)))
 for f in [P/'protocol.json',P/'result.json',P/'extraction_map.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='split_start_byte_exact_restore_and150_CPU_calls_verified',calls_per_flag=75,flags=[0,1],source_sha256=refs,adopted=False,research_complete=False,scope='Private defaultoff start-only INLINEoff extraction from exact two-phase source, unchanged64bit error and original operation statements. Frozen original75command fixture for both flags. No HLS/RTL/full-native or physical result.')
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(report['status'])
if __name__=='__main__':main()
