"""Frozen paired feature-cache microbenchmark; no native routing claims."""
import gc,hashlib,json,statistics,time
from pathlib import Path
from incremental_IPIN_feature_cache_v1 import Cache
from verify_incremental_IPIN_cache_v1_2026_10_18 import check,edits

def main():
 out=Path('experiments/incremental_IPIN_cache_benchmark_v1_2026-10-18');out.mkdir(exist_ok=False)
 proofpath=Path('experiments/incremental_IPIN_cache_verification_v1_2026-10-18/verification.json')
 proof=json.loads(proofpath.read_text());assert proof['status']=='pass'
 for p,digest in proof['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest,p
 g=json.loads(Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json').read_text())
 sizes={v['sink_RR']:len(v['members']) for v in g['groups'] if v['kind']=='direct_sink_IPIN'}
 sources={int(k) for k,v in g['fallback_reasons'].items() if v=='fixed_or_unsupported_type_SOURCE'};epoch=g['graph_sha256']
 pp=json.loads(Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/protocol.json').read_text())
 old=json.loads(Path('experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text())['previous_endpoint']
 paths=[old]+[v['endpoint'] for _,v in sorted(pp['inputs'].items())]
 snapshots=[sorted(json.loads(Path(p).read_text())['connections'],key=lambda r:r['connection_id']) for p in paths]
 protocol=dict(repeats=6,pairs=[[0,i] for i in [1,2,3]],order='alternate incremental-first and rebuild-first per repeat',clock='perf_counter_ns',gc='enabled; collect before each measured operation',shared_metadata='preloaded identical graph domains; file IO excluded from both arms',rebuild='Cache constructor validates full endpoint state and builds sparse features plus NET/source state',incremental='supplied delta prepare+commit only; discovery reported separately',export='full snapshot reported separately; outside both core arms',scope='Existing exposed development placements; component costs only, no full-flow or forecast promotion',bindings={**proof['bindings'],str(proofpath.resolve()):hashlib.sha256(proofpath.read_bytes()).hexdigest(),str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
 with (out/'protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
 records=[]
 def timed(fn):
  gc.collect();start=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-start)/1e6
 for target in [1,2,3]:
  a,b=snapshots[0],snapshots[target]
  for repeat in range(6):
   cache=Cache(epoch,sizes,sources,a)
   delta,discovery=timed(lambda:edits(a,b))
   def update():return cache.commit(cache.prepare(epoch,cache.generation,delta))
   if repeat%2==0:
    receipt,update_ms=timed(update);rebuilt,rebuild_ms=timed(lambda:Cache(epoch,sizes,sources,b))
   else:
    rebuilt,rebuild_ms=timed(lambda:Cache(epoch,sizes,sources,b));receipt,update_ms=timed(update)
   snap,export_ms=timed(cache.snapshot)
   assert snap==rebuilt.snapshot()|{'generation':cache.generation}
   check(cache,b,sizes)
   records.append(dict(case=target,repeat=repeat,incremental_first=repeat%2==0,updates=len(delta),discovery_ms=discovery,prepare_commit_ms=update_ms,rebuild_ms=rebuild_ms,export_ms=export_ms,copied_entries=receipt['copied_shard_entries']))
   del cache,rebuilt,snap
 summary=[]
 for case in [1,2,3]:
  rows=[r for r in records if r['case']==case]
  summary.append(dict(case=case,updates=rows[0]['updates'],**{k:statistics.median(r[k] for r in rows) for k in ['discovery_ms','prepare_commit_ms','rebuild_ms','export_ms']}))
 for p,digest in protocol['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest,p
 with (out/'results.json').open('x') as f:json.dump(dict(status='pass',records=records,median_ms=summary,scope=protocol['scope']),f,indent=2)
 print(json.dumps(summary))
if __name__=='__main__':main()
