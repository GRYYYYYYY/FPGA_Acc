"""Complete manifest CID attribution of actual route-tree seed heap insertions."""
import array,collections,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from native_seed_context_replay_v1 import replay
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';source=E/'mmc_native_connection_seed_context_v1_2026-10-18';rp=source/'cohort_equivalence.json';r=json.loads(rp.read_text());assert len(r['rows'])==6 and r['all6_native_full_output_bytes_integer_counters_equal'];corep=E/'native_seed_context_replay_core_v1_2026-10-18/verification.json';core=json.loads(corep.read_text());assert len(core['corrupt_fixtures_rejected'])==10;cp=E/'mmc_native_connection_CID_binding_v1_2026-10-18/independent_verification_v1.json';cert=json.loads(cp.read_text());qp=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';assert sha(qp)==cert['bindings'][str(qp)];inverse={}
 for line in qp.read_text().splitlines():
  t=line.split()
  if t[0]=='Q':cid,net,pin=map(int,t[1:4]);assert (net,pin) not in inverse;inverse[net,pin]=cid
 assert len(inverse)==115572;out=E/'mmc_native_seed_context_replay_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={**r['bindings'],**{str(p):sha(p) for p in [rp,corep,cp,qp,Path(__file__),R/'tools/native_seed_context_replay_v1.py']}};rows=[]
 with Cache().installed():
  assert all(sha(p)==h for p,h in bindings.items())
  for row in r['rows']:
   case,arm=row['case'],row['arm'];assert row['legacy_owner_and_connection_traces_byte_equal'];folder=source/case/arm;seedcounts=array.array('Q',[0])*115572;uniques=array.array('Q',[0])*115572;calls=array.array('Q',[0])*115572;hist=collections.Counter();pushes=pops=0
   def emit(v):
    nonlocal pushes,pops
    key=(v['native_NET'],v['native_pin']);assert key in inverse;cid=inverse[key];seedcounts[cid]+=v['seed_heap_pushes'];uniques[cid]+=v['unique_seed_RRs'];calls[cid]+=1;hist[v['seed_heap_pushes']]+=1;pushes+=v['all_heap_pushes'];pops+=v['all_heap_pops']
   result=replay(folder/'seed_context.bin',folder/'connection_trace.tsv',emit);assert result['attempts']==row['connection_attempts'] and result['seed_records']==row['route_tree_seed_push_records'] and result['inside_seed_pushes']==row['seed_pushes_inside_attempts'] and result['outside_seed_pushes']==row['seed_pushes_outside_attempts'];assert sum(seedcounts)==result['inside_seed_pushes'] and sum(calls)==result['attempts'];assert pushes==row['attributed_sink_heap_pushes'] and pops==row['attributed_sink_heap_pops'];assert all(u<=s for u,s in zip(uniques,seedcounts));sub=out/(case+'__'+arm);sub.mkdir();vectors={}
   for name,data in [('seed_heap_pushes',seedcounts),('sum_unique_seed_RRs_per_attempt',uniques),('attempts',calls)]:
    p=sub/(name+'.u64');p.write_bytes(data.tobytes());vectors[name]=dict(path=str(p),sha256=sha(p),typecode='Q',itemsize=data.itemsize,values=115572,byteorder=sys.byteorder)
   result.update(case=case,arm=arm,vectors=vectors,all_sink_heap_pushes=pushes,all_sink_heap_pops=pops,seed_share_of_heap_pushes=result['inside_seed_pushes']/pushes,seed_count_histogram=dict(sorted(hist.items())));rows.append(result);print('COMPLETE CID SEED REPLAY PASS',case,arm,result['inside_seed_pushes'],result['outside_seed_pushes'],result['seed_share_of_heap_pushes'],flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as f:json.dump(dict(status='all6_actual_seed_push_streams_and_complete_CID_attributions_pass',bindings=bindings,rows=rows,scope='Measured route-tree seed insertion count and sum of per-attempt unique seed RR counts, complete CID zero domain. All seed pushes in a call may include internal fallback/retry; no initial-phase boundary, prospective geometry predictor or elapsed-time benefit certified.'),f,indent=2)
if __name__=='__main__':main()
