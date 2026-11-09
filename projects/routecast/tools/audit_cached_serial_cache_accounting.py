"""Audit independent process caches, explicitly identify overwritten floor stats."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/owner50_cached_serial_acceptance_workflow_2026-10-07';tag='owner50_cached_serial_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items());rows=[]
for suffix,calls in [('predictor',8),('fallback',10),('cold',12)]:
 base=ROOT/'experiments'/(tag+'_'+suffix);file=base/'rr_cache_stats.json';s=json.loads(file.read_text());assert s==dict(builds=3,hits=calls-3,evictions=0);rows.append(dict(process=suffix,constructor_calls=calls,stats=s,stats_sha256=sha(file)))
floor=ROOT/'experiments'/(tag+'_floor/rr_cache_stats.json');s=json.loads(floor.read_text());assert s['builds']>=1
rows.append(dict(process='floor_independent_proof_last_writer',stats=s,stats_sha256=sha(floor),limitation='prepare and verify share this filename; verification overwrote preparation statistics. These values ONLY describe final verifier process, not preparation; preparation wallclock includes actual startup, but separate preparation cache counts unavailable.'))
(out/'cache_accounting.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),auditor_sha256=sha(Path(__file__)),rows=rows,scope='Each stage executes in its own process and cold cache; predictor/fallback/baseline all have3 actual builds. No crossprocess warmcache assumption. Floor stats lastwriter limitation explicit. Three-entry cap not byte/RSS bound; main selectedimport process stats not emitted. Sourcehashes authenticated.'),indent=2)+'\n');print(rows,flush=True)
