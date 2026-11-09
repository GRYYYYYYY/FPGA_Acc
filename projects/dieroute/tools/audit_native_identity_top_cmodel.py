"""Verify actual worker/snapshot C++ tops against independently audited gold data."""
from pathlib import Path
import hashlib,json,re,subprocess,struct
R=Path(__file__).resolve().parents[1];P=R/'work/native_identity_higher_g_top_cmodel_20261015'
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as v:
  for b in iter(lambda:v.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='terminal_requires_review' and m['returncode']==0
 for obj in [p,json.loads((P/'launch_protocol.json').read_text())]:
  for field in ['source_sha256','input_source_sha256']:
   for f,h in obj.get(field,{}).items():assert sha(f)==h,f
 assert p['compiler_defines']==['DIEROUTE_NATIVE_HIGHER_G_TIE=1'] and len(p['expected_artifacts'])==7
 comparisons={}
 for name,h in p['expected_artifacts'].items():assert sha(P/'artifacts'/name)==h,name;comparisons[name]=h
 for name in ['native_search_worker_hbm.cpp','native_snapshot_search_sharded_hbm.cpp']:assert sha(P/'src'/name)==sha(R/'src'/name)
 symbols=subprocess.check_output(['nm','--defined-only',str(P/'probe')],text=True)
 for name in ['dieroute_native_search_worker_hbm','dieroute_native_snapshot_search_sharded_hbm']:assert re.search(r'\bT '+name+r'\b',symbols),name
 source=(P/'probe.cpp').read_text();assert 'std::array<U,8> result=top_result,meta=top_meta;' in source and 'std::array<U,8> goal=top_goal;' in source and 'auto v=native_search_snapshot_sharded<' not in source
 assert 'actual_worker_equal_f_higher_g_seed_pop_passed calls=8' in (P/'worker_order_check.stdout').read_text()
 result=struct.unpack('<8Q',(P/'artifacts/result.raw').read_bytes());assert result[0]==0 and result[1]==43 and result[5]==256
 files=[P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'stdout.log',P/'stderr.log',P/'worker_order_check.cpp',P/'worker_order_check',P/'worker_order_check.stdout',Path(__file__).resolve()]
 report=dict(status='actual_worker_snapshot_tops_match7_gold_artifacts_and_worker_tie_fixture_passes',seed_calls=1,snapshot_calls=1,worker_fixture_calls=8,expanded=43,observations=256,artifact_comparisons=comparisons,source_sha256={str(f):sha(f) for f in files},scope='Actual unchanged top source files with isolated coherent higher-g queue header flag; full original graph/workspace/identity-hop task, three guarded independent read-only owner arrays. Seven raw top/trace artifacts byte-match independent CPU gold; actual worker seed/pop equal-f ordering exercised separately. C++ C-model only, not RTL co-simulation, HLS synthesis, XRT, physical mapping or performance proof.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','artifact_comparisons']}))
if __name__=='__main__':main()
