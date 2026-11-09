"""Extend the certified original full-input arithmetic domain to frozen factors."""
import datetime,json,resource,sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from neuron_scaled_present_integer_bounds_v1 import bounds
from multiplicative_net_congestion_v1 import cost
# Independent exhaustive finite checks complement the monotone global argument.
checks=0
for owners in range(1,5):
 for factor in (1,2,4):
  for base in (0,1,7):
   for weight in (0,3):
    ceiling=bounds(nodes=5,owners=owners,max_fanout=2,base=base,weight=weight,span=4,root=2,arc=3,denominator=8,factor=factor)['prepared_increment_ceiling']
    for history in range(owners+1):
     for cap in range(5):
      for count in range(owners+1):
       if cap==0 and count:continue
       for span in range(5):
        actual=base*(1+history)*(1+factor*max(0,count-cap+1))+weight*span
        assert 0<=actual-base<=ceiling
        if factor==1:assert actual==cost(base,history,count,cap,False,weight*span)
        checks+=1
case=R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15';launch=json.loads((case/'launch_observation_v1.json').read_text());p=Path('/proc')/str(launch['model_pid']);s=(p/'stat').read_text().rsplit(')',1)[1].split();assert int(s[19])==launch['model_startticks'] and s[0]!='Z'
vm=int(next(x for x in (p/'status').read_text().splitlines() if x.startswith('VmSize:')).split()[1])*1024;reserve=max(0,20*2**30-vm);limit=512*2**20;free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());admission=dict(shared_headroom_bytes=free,remaining_live_model_reservation_bytes=reserve,child_limit_bytes=limit,margin_bytes=8*2**30,admitted=free>=reserve+limit+8*2**30);assert admission['admitted'],'Bounds audit not launched: memory admission unavailable'
resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
hp=R/'experiments/neuron_exact_hardware_cost_width_v1_2026-10-13/verification.json';bp=R/'experiments/titan23_neuron_node_base_wide_v1_2026-10-13/verification.json';lp=R/'experiments/titan23_neuron_graph_recovery_v1_2026-10-13/lattice_readiness.json';ep=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
h=json.loads(hp.read_text());assert h['all_pass'] and h['fixed_rounds']==2 and h['normalized_perpin_numerators_all_exact'];assert all(sha(p)==v for p,v in h['bindings'].items())
b=json.loads(bp.read_text());l=json.loads(lp.read_text());e=json.loads(ep.read_text());counts=Counter(q['net_id'] for q in e['connections']);assert len(counts)==h['owners']==50767 and len(e['connections'])==h['connections']==77106
D=h['common_criticality_denominator'];assert D<2**64 and all(D%int(d)==0 for d in h['denominator_histogram']) and sum(h['denominator_histogram'].values())==77106
kwargs=dict(nodes=h['nodes'],owners=h['owners'],max_fanout=max(counts.values()),base=b['maximum_node_base'],weight=l['static_span_price_weight'],span=h['maximum_channel_span'],root=l['maximum_root_word'],arc=l['maximum_arc_word'],denominator=D)
rows=[bounds(**kwargs,factor=f) for f in (1,2,4)]
assert rows[0]['maximum_semantic_total_node_price']==h['conservative_snapshot_congestion_upper_bound'] and rows[0]['raw_simple_path_upper_bound']==h['raw_simple_path_upper_bound'] and rows[0]['whole_NET_objective_upper_bound']==h['whole_NET_objective_upper_bound']
assert all(x['price_store128_admitted'] and x['native_raw128_admitted'] and x['native_weighted240_admitted'] and x['chosen_common_arithmetic_lane_bits']<=160 for x in rows)
assert all(x['legacy120_must_reject_this_ceiling'] for x in rows[1:])
bindings={**closure([Path(__file__)]),**h['bindings'],**{str(p):sha(p) for p in [hp,bp,lp,ep]}}
assert all(sha(p)==v for p,v in bindings.items())
result=dict(bindings=bindings,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),all_pass=True,resource_admission=admission,complete_graph_nodes=h['nodes'],complete_connections=77106,complete_NETs=50767,input_bounds=kwargs,rows=rows,exhaustive_small_domain_cases=checks,exact_factor1_reproduces_original_certificate=True,all_original_perpin_denominators_divide_common=True,assumptions=['Exactly two feedback rounds; initial accumulated-history update skipped, so only one occupancy-overuse history addition.','Whole-NET unique ownership counts<=50767; zero-capacity resources have no owner.','Original graph, structural base, span, RC lattice and frozen initialized binary32 criticality epoch unchanged.','Semantic upper bound and supplied prepare ceiling are different quantities; both are covered.'],scope='Full-input certificate extension plus exhaustive finite algebra checks, not a new search/model or hardware run. Factors2/4 large-graph models and their independent audits remain pending;160bit arithmetic range is not RTL, synthesis, timing, throughput or board proof. Legacy120 rejection applies to the supplied worst-case prepare ceiling, not all realized paths or arbitrary tighter ceilings.')
out=R/'experiments/neuron_scaled_present_integer_bounds_v1_2026-10-15';out.mkdir();(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(all_pass=True,small_domain_checks=checks,factors=[{k:x[k] for k in ['factor','price_bits','semantic_queue_bits','native_weighted_guard_bits','signed_objective_delta_bits','chosen_common_arithmetic_lane_bits','legacy120_must_reject_this_ceiling']} for x in rows]),indent=2),flush=True)
