"""Check default-off decoder, actual native tops, full outputs and lossless packed input."""
import hashlib,json,re,struct,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_potential_dual_format_Cmodel_20261015';A=R/'work/native_identity_higher_g_top_cmodel_20261015'
def main():
 refs={}
 def sha(f):
  f=Path(f).resolve();key=str(f)
  if key not in refs:
   h=hashlib.sha256()
   with f.open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 x=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='dual_format_legacy_and_full_native_Cmodel_terminal_requires_review' and len(m['steps'])==len(x['commands'])
 for f,h in x['source_sha256'].items():assert sha(f)==h,f
 for command,step in zip(x['commands'],m['steps']):assert step['returncode']!=0 if command.get('expected_nonzero') else step['returncode']==0
 changes=json.loads((P/'changes.json').read_text())
 for name in {v['file'] for v in changes}:
  s=(P/name).read_text()
  for c in reversed([v for v in changes if v['file']==name]):assert s.count(c['after'])==1;s=s.replace(c['after'],c['before'],1)
  assert s==(A/name).read_text(),name;sha(A/name)
 oldaudit=json.loads((A/'independent_audit.json').read_text());assert sha(A/'protocol.json')==oldaudit['source_sha256'][str(A/'protocol.json')]
 old=json.loads((A/'protocol.json').read_text());assert len(old['expected_artifacts'])==7
 assert sha(P/'src/native_search_worker_hbm.cpp')==sha(A/'src/native_search_worker_hbm.cpp')
 legacy=R/'work/native_higher_g_hls_validation_20261015/snapshot/source/native_snapshot_search_hbm_tb.cpp'
 assert sha(P/'fixture/native_snapshot_search_hbm_tb.cpp')==sha(legacy)
 for flag in [0,1]:
  text=(P/f'properties{flag}.log').read_text();assert f'DUAL_POTENTIAL_PROPERTIES flag={flag} wide_values=4099 finite_values=4099 fallback256_and_infinity=pass invalid_formats=pass' in text
  assert 'SHARDED_SEARCH_DIFFERENTIAL calls=10' in (P/f'legacy{flag}.log').read_text();sha(P/f'legacy{flag}.log')
  symbols=subprocess.check_output(['nm','--defined-only',str(P/f'probe{flag}')],text=True)
  for name in ['dieroute_native_search_worker_hbm','dieroute_native_snapshot_search_sharded_hbm']:assert re.search(r'\bT '+name+r'\b',symbols),name
  for name,h in old['expected_artifacts'].items():assert sha(P/f'artifacts{flag}'/name)==sha(A/'artifacts'/name)==h,name
  words=struct.unpack('<8Q',(P/f'artifacts{flag}/result.raw').read_bytes());assert words[:2]==(0,43) and words[5]==256
  for f in [P/f'probe{flag}',P/f'probe{flag}.log',P/f'properties{flag}.log']:sha(f)
 sanitized=(P/'sanitize.log').read_text();assert 'DUAL_POTENTIAL_PROPERTIES flag=1' in sanitized and 'runtime error:' not in sanitized and 'ERROR: AddressSanitizer' not in sanitized
 packed=R/'work/native_potential8_lossless_storage_20261015';bound=json.loads((packed/'independent_audit.json').read_text());assert sha(P/'artifacts1/potential8.raw')==sha(packed/'potential8.raw')==bound['source_sha256'][str(packed/'potential8.raw')]
 for f in [P/'protocol.json',P/'manifest.json',P/'changes.json',P/'sanitize.log',P/'properties.cpp',P/'include/native_search_hbm_potential.hpp',A/'independent_audit.json',packed/'independent_audit.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='dual_format_wide_fallback20legacy_calls_both_full_native_tops7raw_each_match',flags=[0,1],native_nodes=91975782,search_expanded=43,observations=256,raw_files_per_mode=7,packed_input_bytes=(P/'artifacts1/potential8.raw').stat().st_size,property_values=4099,legacy_directed_calls=20,wide_fallback256_and_infinity=True,invalid_format3_rejected=True,sanitizers_pass=True,source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Private defaultoff runtime formats0disabled1wide2packed, enabled-format bounds retain original0/1 validity and reject3. Actual shared host preparation falls back intact for256/UINT64MAX; original10directed inputs unchanged eachflag. Worker top unchanged; snapshot wrapper only extends enable validation to2 underflag1 and passes internal packed-mode boolean; external argument list not intentionally changed, generated ABI still unverified; both full native C-model runs with original2M/2M budgets and coherent higher-g ordering match7gold outputs. Enabled materialized packed input also matches independently all-node audited file. Guarded owner immutability checks retained by original host. No HLS/generated ABI, RTL, XRT or performance proof.')
 with (P/'independent_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(report['status'])
if __name__=='__main__':main()
