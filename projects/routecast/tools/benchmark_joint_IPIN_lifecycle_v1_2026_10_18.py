"""Balanced joint-state component clocks including predecessor view release."""
import gc,hashlib,json,statistics,time
from pathlib import Path
from joint_IPIN_state_v1 import Joint
from verify_incremental_IPIN_cache_v1_2026_10_18 import edits
from verify_joint_IPIN_state_v1_2026_10_18 import verify

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/joint_IPIN_lifecycle_benchmark_v1_2026-10-18');out.mkdir(exist_ok=False)
 proofpath=Path('experiments/joint_IPIN_state_verification_v1_2026-10-18/verification.json');proof=json.loads(proofpath.read_text());assert proof['status']=='pass'
 bindings=proof['bindings']
 for p,h in bindings.items():assert sha(p)==h
 bindings={**bindings,str(proofpath.resolve()):sha(proofpath),str(Path(__file__).resolve()):sha(__file__)}
 gp=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json');g=json.loads(gp.read_text());epoch=g['graph_sha256']
 groups={v['sink_RR']:v['members'] for v in g['groups'] if v['kind']=='direct_sink_IPIN'};sources={int(k) for k,v in g['fallback_reasons'].items() if v=='fixed_or_unsupported_type_SOURCE'}
 config=json.loads(Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/protocol.json').read_text())
 old=json.loads(Path('experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text())['previous_endpoint']
 paths=[old]+[v['endpoint'] for _,v in sorted(config['inputs'].items())];snapshots=[sorted(json.loads(Path(p).read_text())['connections'],key=lambda r:r['connection_id']) for p in paths]
 protocol=dict(bindings=bindings,repeats=6,cases=[1,2,3],order='alternate incremental and rebuild first',clock='perf_counter_ns',gc='enabled, full collection immediately before each arm outside timer',lifecycle='one captured predecessor view released within timer; unchanged current state remains live; no other stale tickets/readers',included='incremental prepare+commit+old-view release; rebuild complete Joint+old-object/view release',excluded='initial old-state construction, graph/endpoint file IO, delta discovery (reported separately), full export, channels/native, explicit cyclic GC',scope='Preloaded exposed development cohort; component comparison only')
 with (out/'protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
 records=[]
 def arm(case,incremental,delta):
  obj=Joint(epoch,groups,sources,snapshots[0]);old_view=obj.view();gc.collect();start=time.perf_counter_ns()
  if incremental:receipt=obj.commit(obj.prepare(epoch,0,delta))
  else:obj=Joint(epoch,groups,sources,snapshots[case]);receipt=None
  del old_view
  elapsed=(time.perf_counter_ns()-start)/1e6
  verify(obj.view(),snapshots[case],groups)
  return elapsed,receipt
 for case in [1,2,3]:
  for repeat in range(6):
   start=time.perf_counter_ns();delta=edits(snapshots[0],snapshots[case]);discovery=(time.perf_counter_ns()-start)/1e6
   if repeat%2==0:inc,receipt=arm(case,True,delta);full,_=arm(case,False,delta)
   else:full,_=arm(case,False,delta);inc,receipt=arm(case,True,delta)
   records.append(dict(case=case,repeat=repeat,incremental_first=repeat%2==0,updates=len(delta),discovery_ms=discovery,incremental_lifecycle_ms=inc,rebuild_lifecycle_ms=full,score_updates=receipt['score_updates']))
 medians=[dict(case=case,**{key:statistics.median(r[key] for r in records if r['case']==case) for key in ['discovery_ms','incremental_lifecycle_ms','rebuild_lifecycle_ms']}) for case in [1,2,3]]
 for p,h in bindings.items():assert sha(p)==h
 with (out/'results.json').open('x') as f:json.dump(dict(status='pass',records=records,medians=medians,scope=protocol['scope']),f,indent=2)
 print(json.dumps(medians))
if __name__=='__main__':main()
