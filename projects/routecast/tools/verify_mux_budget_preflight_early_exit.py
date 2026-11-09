"""Bind early-exit decisions to fullgraph minima and frozen inputs."""
import json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_budget_preflight_early_exit_2026-10-06';baseline=ROOT/'experiments/mux_budget_preflight_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());bp=json.loads((baseline/'protocol.json').read_text());br=json.loads((baseline/'receipt.json').read_text());assert p['cases']==bp['cases']and r['protocol_sha256']==sha(out/'protocol.json')and br['protocol_sha256']==sha(baseline/'protocol.json');assert all(sha(f)==h for c in p['cases']for f,h in c['inputs'].items());rows=[]
for a,b in zip(r['rows'],br['rows']):
 w=a['width'];assert w==b['width'];ef=out/f'w{w}.json';bf=baseline/f'w{w}.json';assert sha(ef)==a['observation_sha256']and sha(bf)==b['observation_sha256'];early=json.loads(ef.read_text());full=json.loads(bf.read_text());assert early['scale']==full['scale']and early['affected']==full['affected'];assert [o['query']for o in early['observations']]==[o['query']for o in full['observations'][:len(early['observations'])]]
 for e,f in zip(early['observations'],full['observations']):
  assert e['budget_units']==f['budget_units']and e['feasible']==f['feasible']
  if e['feasible']:assert e['minimum_units']==f['minimum_units']and Fraction(e['minimum_ns'])==Fraction(f['minimum_ns'])
  else:assert e['minimum_units']is None and f['minimum_units']>e['budget_units']
 assert len(early['observations'])==a['checked_connections'];assert all(o['feasible']for o in early['observations'][:-1])and not early['observations'][-1]['feasible'];assert a['status']==b['status']=='REJECT_BUDGET_CANDIDATE_USE_NATIVE_COLD'
 rows.append(dict(width=w,checked_connections=a['checked_connections'],available_connections=a['budgeted_affected_connections'],first_failed_query=early['observations'][-1]['query'],decision_parity=True,preflight_seconds=a['preflight_seconds'],full_preflight_seconds=b['preflight_seconds'],fresh_context_overhead_seconds=a['context_bind_seconds']+a['preflight_seconds']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),baseline_receipt_sha256=sha(baseline/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='All38observedquery classifications and feasibleminima matchfullDijkstra; exactdecisionparity current3cases. Single-run timings, not total acceleration, generic policy correctness or independent minproof for every query.'),indent=2)+'\n');print(rows)
