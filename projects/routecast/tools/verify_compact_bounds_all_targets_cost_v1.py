"""Independently check full input target coverage, cold/warm counts and payload."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/compact_bounds_all_targets_cost_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';result=json.loads(p.read_text());plan=json.loads((D/'protocol.json').read_text());assert result['protocol']==plan;assert all(sha(k)==h for k,h in plan['bindings'].items())
 baseline=next(Path(k) for k in plan['bindings'] if k.endswith('/round1.json'));budgets={}
 for q in json.loads(baseline.read_text())['records']:budgets.setdefault(q['sink'],set()).add(q['budget_integer'])
 events=[json.loads(s) for s in (D/'cold_events.jsonl').read_text().splitlines()];assert [q['target'] for q in events]==sorted(budgets);assert [q['index'] for q in events]==list(range(1,len(budgets)+1));assert all(q['seconds']>=0 for q in events)
 stats=result['final_stats'];n=stats['nodes'];payload=0
 for event in events:
  cap=max(budgets[event['target']])+1;width=next(w for w in (1,2,4,8,16,17) if cap.bit_length()<=8*w);payload+=width*n;assert event['cached_payload_bytes']==payload
 pairs=sum(map(len,budgets.values()));assert stats['cached_targets']==stats['misses']==len(budgets)==plan['targets'];assert stats['hits']==pairs==plan['target_budget_pairs'];assert stats['cached_payload_bytes']==stats['peak_cached_payload_bytes']==payload<=plan['payload_limit_bytes'];assert stats['growth_rebuilds']==stats['evictions']==stats['uncached_vectors']==0;assert result['cold_stats']['hits']==0;assert result['cold_stats']['misses']==len(budgets);assert sum(e['seconds'] for e in events)<=result['cold_seconds'];assert result['warm_seconds']>=0
 report=dict(status='FULL_INPUT_COVERAGE_PACKED_PAYLOAD_COLD_WARM_ACCOUNTING_VERIFIED',targets=len(budgets),target_budget_pairs=pairs,retained_payload_bytes=payload,cold_seconds=result['cold_seconds'],warm_seconds=result['warm_seconds'],bindings={str(k):sha(k) for k in [Path(__file__),p,D/'protocol.json',D/'cold_events.jsonl']},scope='Accounting verifier only; all-node lower-bound parity is established separately by microbenchmark/random contracts, not asserted here. No predictor forecast or paid speed claim.')
 (D/'independent_accounting_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
