"""Signed phase work deltas for every fixed case; retain gains and regressions."""
import pathlib,json,hashlib,re
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 T=R/'experiments/mmc_first_iteration_hint_trace_replay_v1_2026-10-19';vp=T/'verification.json'
 if not vp.exists():raise SystemExit('NOT_READY: authoritative complete6 replay required; no output created')
 v=json.loads(vp.read_text());assert v['status']=='all6_first_iteration_hint_native_traces_independently_replayed';O=R/'experiments/mmc_first_hint_work_phase_diagnosis_v1_2026-10-19';O.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [vp,pathlib.Path(__file__).resolve()]};rows=[];keys=['NET_operations','connection_operations','heap_pushes','heap_pops']
 for case in ['episode_01','episode_02','episode_03']:
  arms={}
  for arm in ['zero','forecast']:
   p=T/(case+'_'+arm+'.json');assert v['bindings'][str(p)]==sha(p);a=json.loads(p.read_text());stats=a['iteration_stats'];assert len(stats)>1;first={k:stats[0][k] for k in keys};later={k:sum(x[k] for x in stats[1:]) for k in keys};total={k:first[k]+later[k] for k in keys};log=R/'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19'/case/arm/'cold/native.log';assert a['bindings'][str(log)]==sha(log);raw=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',log.read_text());assert len(raw)==1 and tuple(total.values())==tuple(map(int,raw[0]));arms[arm]=dict(iterations=len(stats),first=first,later=later,total=total,later_heap_pushes_per_connection=str(Fraction(later['heap_pushes'],later['connection_operations'])));bindings[str(p)]=sha(p);bindings[str(log)]=sha(log)
  z,f=arms['zero'],arms['forecast'];delta={s:{k:f[s][k]-z[s][k] for k in keys} for s in ['first','later','total']};assert all(delta['first'][k]+delta['later'][k]==delta['total'][k] for k in keys);rows.append(dict(case=case,arms=arms,forecast_minus_zero_work_deltas=delta,later_heap_pushes_per_connection_ratio=str(Fraction(f['later']['heap_pushes'],f['later']['connection_operations'])/Fraction(z['later']['heap_pushes'],z['later']['connection_operations']))));print('FIRST_HINT_SIGNED_PHASE_DELTAS',case,delta,flush=True)
 (O/'review.json').open('x').write(json.dumps(dict(status='ALL6_FIRST_HINT_SIGNED_WORK_PHASE_DELTAS_MATCH_RAW_NATIVE_TOTALS',cases=rows,bindings=bindings,scope='Exact measured operation attribution, not elapsed-time split or perRR causal explanation. All fixed cases, including unfavorable ones, retained; stopping rounds differ naturally. No stage-fraction division by potentially negative total deltas, no original metric/gate/TTL/seed tuning and no full-flow speedup claim.'),indent=2)+'\n')
if __name__=='__main__':main()
