"""Restore extracted operation bodies and check all75 command differentials."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_phase_boundaries_20261015'
def main():
 refs={}
 def sha(f):
  h=hashlib.sha256(Path(f).read_bytes()).hexdigest();refs[str(f)]=h;return h
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((P/'manifest.json').read_text());assert m['status']=='CPU_differential_complete_requires_review' and len(m['steps'])==3 and all(v['returncode']==0 for v in m['steps'])
 mapping=json.loads((P/'phase_map.json').read_text());s=(P/'source/net_commit_sharded_hbm.cpp').read_text();assert len(mapping)==6 and 'std::uint64_t error=0;' in s
 for item in mapping:
  assert s.count(item['helper'])==1 and s.count(item['call'])==1
  assert '#pragma HLS INLINE off' in item['helper'] and item['original_body'] in item['helper']
  s=s.replace(item['helper'],'').replace(item['call'],'{'+item['original_body']+'}')
 assert s==(R/'src/net_commit_sharded_hbm.cpp').read_text()
 log=(P/'step2.log').read_text();assert 'SHARDED_DIFFERENTIAL calls=75 isolated_owner_banks=3' in log and 'launches=36' in log and 'calls=39' in log
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'phase_map.json',P/'step2.log',P/'command_differential',Path(__file__).resolve()]:sha(f)
 result=dict(status='six_phase_extraction_exact_restore_and75_CPU_byte_differentials_pass',phases=[v['phase'] for v in mapping],differential_calls=75,source_sha256=refs,scope='Six exact body extractions restore byte-identical production source, preserving64bit error and all interfaces/budgets; full original75guarded flat/sharded command comparisons pass onCPU. Scheduling, RTL and physical benefit unproved.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'])
if __name__=='__main__':main()
