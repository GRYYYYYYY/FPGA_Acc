"""Check default-off conservative filter, invariants, baseline traces and poststates."""
import hashlib,json,re
from pathlib import Path
from zipfile import ZipFile
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_key_filter_variant_20261015'
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
 x=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='all_CPU_checks_terminal_requires_review'
 assert [v['name'] for v in m['steps']]==[v['name'] for v in x['commands']]
 for a,b in zip(x['commands'],m['steps']):assert b['returncode']!=0 if a.get('expected_nonzero') else b['returncode']==0
 assert 'DIEROUTE_COMMIT_KEY_FILTER_must_be_0_or_1' in (P/'invalid_flag.log').read_text()
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 original=(P/'source/net_commit_sharded_hbm.cpp').read_text()
 for c in reversed(json.loads((P/'changes.json').read_text())):assert original.count(c['after'])==1;original=original.replace(c['after'],c['before'])
 xo=R/'work/native_higher_g_hw_emu_link_20261015/commit.xo'
 with ZipFile(xo) as z:assert original.encode()==z.read('dieroute_net_commit_sharded_hbm/cpu_sources/net_commit_sharded_hbm.cpp')
 gold=R/'work/native_identity_higher_g_commit_differential_20261015';bound=json.loads((gold/'independent_audit.json').read_text());assert bound['all_net_trees_checked']==341
 profiles={}
 for flag in [0,1]:
  suite=(P/f'suite{flag}.log').read_text();assert 'SHARDED_DIFFERENTIAL calls=75 isolated_owner_banks=3' in suite and 'launches=36' in suite and 'calls=39' in suite
  log=(P/f'actual{flag}.log').read_text();assert 'SHARDED_DIFFERENTIAL calls=43 isolated_owner_banks=3' in log
  rows=[{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)} for line in log.splitlines() if line.startswith('COMMIT_LOGICAL ')]
  assert len(rows)==43 and [v['op'] for v in rows]==[3]+[7]*42 and all(v['status']==0 for v in rows)
  profiles[str(flag)]=rows
  for name in ['canonical_reads.raw','control.raw','nets.raw','proposal_completion.raw','resources.raw','trees.raw']:
   f=gold/'artifacts'/name;assert sha(f)==bound['source_sha256'][str(f)];assert sha(P/f'actual{flag}'/name)==sha(f),name
  sha(P/f'suite{flag}.log');sha(P/f'actual{flag}.log');sha(P/f'profile{flag}');sha(P/f'suite{flag}')
 a=profiles['0'][0];b=profiles['1'][0];assert a['load_key_tests']==3444 and a['store_key_tests']==3655
 for old,new in zip(profiles['0'],profiles['1']):
  for key in old:
   if key in ['load_key_tests','store_key_tests']:assert new[key]<=old[key]
   else:assert old[key]==new[key],key
 assert b['load_key_tests']+b['store_key_tests']<a['load_key_tests']+a['store_key_tests']
 for name in ['properties.log','properties_sanitize.log']:
  log=(P/name).read_text();assert 'FILTER_PROPERTIES insertions=20000 saturation_bits=256 reset_epochs=20' in log and 'runtime error:' not in log and 'ERROR: AddressSanitizer' not in log;sha(P/name)
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'changes.json',P/'profiled_changes.json',P/'invalid_flag.log',P/'filter_properties.cpp',P/'filter_properties_sanitize',gold/'independent_audit.json',Path(__file__).resolve()]:sha(f)
 result=dict(status='defaultoff_key_filter150suite86nativecalls_properties_sanitizers_poststate_parity_pass',suite_calls=150,native_calls=86,insert_property_checks=20000,reset_property_epochs=20,saturation_bits=256,proposal_before=a,proposal_after=b,logical_key_tests_before=a['load_key_tests']+a['store_key_tests'],logical_key_tests_after=b['load_key_tests']+b['store_key_tests'],source_sha256=refs,scope='Original monolithic commit variant, same complete nativegraph/authority and actual XRT path, flags0/1. Original75suite each and43native calls each guarded flat/sharded byte parity;6poststate files match341tree gold. Fixed256bit one-sided filter uses onlynegative answers to skip scans; positives retain exact fullkey comparison, no capacity/budget change.20kmarked-key/reset/saturation properties andASAN/UBSAN pass. Counts are C++ logical probes, not bus/cycles/FPGA speedup; no RTL, physical, root-cause or adoption result.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:result[k] for k in ['status','logical_key_tests_before','logical_key_tests_after']}))
if __name__=='__main__':main()
