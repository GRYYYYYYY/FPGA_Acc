"""Matched ABBA controlled corpus; timings include unsuccessful proposal/fallback work."""
import json,time,sys
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from hybrid_bidirectional_search_v1 import Search as Original
from compatible_multi_bidi_search_v1 import Search as Candidate

def main():
 m=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10/model'
 out=R/'experiments/mmc_compatible_small_target_matched_corpus_v1_2026-10-10';out.mkdir(exist_ok=True)
 receipt=json.loads((m/'receipt.json').read_text())
 bindings={**receipt['bindings'],**receipt['files']}
 assert all(sha(p)==h for p,h in bindings.items())
 endpoint=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'
 tick=time.perf_counter();_,_,_,f,rc,queries=load_endpoints(endpoint);load_seconds=time.perf_counter()-tick
 groups=defaultdict(list)
 for q in queries:groups[q['net_id']].append(q)
 phases=[({},0,sorted(groups))]
 for row in receipt['rounds']:
  state=json.loads(Path(row['state_file']).read_text())
  phases.append(({int(k):v for k,v in state['prices'].items()},rc.scale//(20*10**9),row['affected_nets']))
 phases=[(prices,weight,[net for net in nets if 2<=len({q['sink'] for q in groups[net]})<=4]) for prices,weight,nets in phases]
 binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
 reference={};runs=[]
 for label in ['original','candidate','candidate','original']:
  tick=time.perf_counter();search=(Original if label=='original' else Candidate)(f,rc,binary);setup=time.perf_counter()-tick
  paid=prepare=audit=0.;count=paths=different=0
  try:
   for phase,(prices,weight,nets) in enumerate(phases):
    tick=time.perf_counter();search.prepare(prices,weight);prepare+=time.perf_counter()-tick
    for net in nets:
     qs=groups[net];src=qs[0]['source'];targets={q['sink'] for q in qs}
     tick=time.perf_counter();raw,parents,settled=search.search(src,targets);paid+=time.perf_counter()-tick
     tick=time.perf_counter();assert targets<=settled
     for dst in sorted(targets):
      u=dst;seen={u};slots=[];delay=rc.initial(src);priced=0
      while u!=src:
       prev,slot=parents[u];assert f['row_offsets'][prev]<=slot<f['row_offsets'][prev+1]
       assert f['dest_ranks'][slot]==u and f['capacities'][u]>0
       slots.append(slot);delay+=rc.increments[slot];priced+=prices.get(u,0);u=prev
       assert u not in seen;seen.add(u)
      assert f['capacities'][src]>0 and delay==raw[dst]
      physical=[f['edge_ids'][e] for e in reversed(slots)]
      assert rc.path(src,dst,physical)==delay
      objective=delay+weight*priced;key=(phase,net,dst)
      if key not in reference:reference[key]=(objective,delay,physical)
      else:
       assert objective==reference[key][0]
       different+=physical!=reference[key][2]
       if not weight:assert delay==reference[key][1]
      paths+=1
     audit+=time.perf_counter()-tick;count+=1
   runs.append(dict(variant=label,constructor_seconds=setup,prepare_seconds=prepare,search_seconds=paid,path_audit_seconds=audit,requests=count,unique_target_paths=paths,paths_different_from_first_original=different,stats=dict(getattr(search,'stats',{}))))
   print(json.dumps(runs[-1]),flush=True)
  finally:search.close()
 expected=sum(len(nets) for _,_,nets in phases)
 assert expected>0 and all(x['requests']==expected for x in runs)
 for p in [Path(__file__).resolve(),endpoint,m/'receipt.json']:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items())
 original=sum(x['search_seconds'] for x in runs if x['variant']=='original')/2
 candidate=sum(x['search_seconds'] for x in runs if x['variant']=='candidate')/2
 (out/'verification.json').write_text(json.dumps(dict(bindings=bindings,load_seconds=load_seconds,runs=runs,original_mean_search_seconds=original,candidate_mean_search_seconds=candidate,candidate_over_original=candidate/original,all_requested_physical_exact_RC_minimum_objectives_pass=True,scope='Exposed MMC all 2-4 unique-target requests, fixed certified original-model price/schedule controlled ABBA; fresh contexts, all attempts and forward fallback inside search clock. Audits/prepares/construction separately timed. Not native, full corpus, fresh endogenous feedback, independent optimum solver, or wholeworkflow gain.'),indent=2)+'\n')
 print('MATCHED CORPUS PASS',candidate/original,flush=True)
if __name__=='__main__':main()
