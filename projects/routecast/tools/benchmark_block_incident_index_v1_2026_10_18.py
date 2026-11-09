"""Sparse delta discovery parity/cost on previously admitted development swaps."""
import sys,json,time,statistics,gc
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from block_incident_connection_index_v1 import build_index,discover

def main():
 seed=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed';rp=seed/'rr/mmc/endpoints.json';mp=seed/'rr/mmc/mapping.json';sp=seed/'demand/mmc/endpoints.json';pp=seed/'demand/mmc/scope_partition.json';swp=R/'experiments/prospective_layout_swap_real_MMC_v1_2026-10-18/verification.json';pinproof=R/'experiments/prospective_layout_swap_native_pin_identity_v1_2026-10-18/verification.json';proof=json.loads(pinproof.read_text())
 for p,h in proof['bindings'].items():assert sha(p)==h
 paths=[rp,mp,sp,pp,swp,pinproof,Path(__file__),R/'tools/block_incident_connection_index_v1.py'];raw=json.loads(rp.read_text());mapping=json.loads(mp.read_text());source=json.loads(sp.read_text())['connections'];translation=[v['original_connection_id'] for v in json.loads(pp.read_text())['physical_to_original_connection_ids']];swaps=json.loads(swp.read_text())['episodes'];out=R/'experiments/prospective_block_incident_index_v1_2026-10-18';out.mkdir(exist_ok=False)
 tick=time.perf_counter_ns();index=build_index(raw,mapping,translation);initial_ms=(time.perf_counter_ns()-tick)/1e6;records=[]
 def timed(fn):
  gc.collect();t=time.perf_counter_ns();r=fn();return r,(time.perf_counter_ns()-t)/1e6
 for e in swaps:
  p=R/f'experiments/prospective_layout_swap_native_partition_v1_2026-10-18/episode_{e["episode"]:02}/endpoints.json';paths.append(p);target=json.loads(p.read_text())['connections']
  def full():return [dict(old=a,new=b) for a,b in zip(source,target) if a!=b]
  for repeat in range(6):
   if repeat%2==0:sparse,sparse_ms=timed(lambda:discover(index,e['changed_blocks'],source,target));reference,full_ms=timed(full)
   else:reference,full_ms=timed(full);sparse,sparse_ms=timed(lambda:discover(index,e['changed_blocks'],source,target))
   delta,candidates=sparse;assert delta==reference;records.append(dict(episode=e['episode'],repeat=repeat,candidates=candidates,changes=len(delta),sparse_ms=sparse_ms,full_scan_ms=full_ms))
 bindings={str(p):sha(p) for p in paths};summary=[dict(episode=i,candidates=next(r['candidates'] for r in records if r['episode']==i),changes=next(r['changes'] for r in records if r['episode']==i),sparse_ms=statistics.median(r['sparse_ms'] for r in records if r['episode']==i),full_scan_ms=statistics.median(r['full_scan_ms'] for r in records if r['episode']==i)) for i in [1,2,3]]
 with (out/'verification.json').open('x') as f:json.dump(dict(status='all18_sparse_discovery_results_equal_complete_scans',bindings=bindings,index_initial_ms=initial_ms,block_index_entries=len(index),records=records,median_ms=summary,scope='Preloaded physical pin records, source/target arrays and complete verified moved-block list. Index initialization measured separately; file IO, admission, full snapshot export, estimator/native routing excluded. No end-to-end speedup. Sparse discovery contract cannot detect unreported/nonlocal target changes; prior full physical/native pin proofs supply that invariant for these three fixtures.'),f,indent=2)
 print(json.dumps(dict(index_initial_ms=initial_ms,median_ms=summary),indent=2))
if __name__=='__main__':main()
