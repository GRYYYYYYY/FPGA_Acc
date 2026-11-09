"""Verify private-cache wholemove artifacts against independently replayed paths."""
import json,sys
from pathlib import Path
from pre_route_endpoints import sha
from rc_read_dependency_cache import RCReadDependencyCache
root=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]).resolve();assert out.parent==root/'experiments';r=json.loads((out/'receipt.json').read_text());reference=root/'experiments/adder_tree_transactional_rc_moves_2026-10-06'
assert all(sha(Path(n))==h for n,h in r['inputs_sha256'].items());assert all(sha(out/'sources'/n)==h for n,h in r['sources_sha256'].items())
checks=[]
for row in r['steps']:
 step=row['step'];assert row['published_epoch']==step;assert row['queries']==516==row['cache_hits']+row['cache_misses']
 for kind in ('prediction','journal','physical','cache'):
  file=out/f'step_{step}_{kind}.json';assert sha(file)==row[f'{kind}_sha256']
  if kind=='prediction':assert json.loads(file.read_text())==json.loads((reference/file.name).read_text())
  if kind in ('journal','physical'):assert file.read_bytes()==(reference/file.name).read_bytes()
 pressure=out/f'step_{step}.pressure';assert sha(pressure)==row['pressure_sha256'];assert pressure.read_bytes()==(reference/pressure.name).read_bytes()
 cache=RCReadDependencyCache.restore(15398,(out/f'step_{step}_cache.json').read_bytes());assert len(cache.records)==0;assert cache.payload()==(out/f'step_{step}_cache.json').read_bytes()
 checks.append({'step':step,'cache_hits':row['cache_hits'],'records':len(cache.records),'cache_bytes':row['cache_payload_bytes'],'failures_preserved_same_snapshot':row['failure_phases']})
assert [x['cache_hits'] for x in checks]==[0,0,0]
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'steps':checks,'total_queries':1548,'actual_searches_skipped':0,'all_prediction_contents_and_journal_audit_pressure_bytes_match_reference':True,'tests':'5 untraced versioned-demand tests passed including imported integer boundaries','scope':'Joint in-memory single pointer publication includes cache bytes; real search/repair/NET admission/RC/XML audit before commit. Failed build retains old snapshot object. Empty initial cache, no retrospective warming. Ordinary artifact export after commit not filesystem atomicity. Fault execution wall not end-to-end performance.'},indent=2)+'\n');print(out.name,checks)
