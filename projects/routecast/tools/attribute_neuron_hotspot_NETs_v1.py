"""Post-label NET/transaction attribution for all frozen predicted/true top20 bins.

Reads complete certified original inputs, without replacing the primary cohort,
metrics or current solver. Memory admission reserves the live solver's remaining
address-space allowance plus 8 GiB before permitting this 512 MiB analysis.
"""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from fractions import Fraction
import argparse
import json
from pathlib import Path
import resource
import sys
import time

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from bounded_model_json_stream_v1 import object_members,round_events
from hotspot_NET_attribution_v1 import domain,model_owners,native_owners,incidences,components
from observe_neuron_compiled_pipeline_v1 import snapshot

OUT=R/'experiments/neuron_hotspot_NET_attribution_v1_2026-10-15'
METRICS=R/'experiments/neuron_certified_native_metrics_v1_2026-10-15'
MODEL=R/'experiments/titan23_neuron_compact_wide_retained_pipeline_v3_2026-10-13/model'
NATIVE=R/'experiments/titan23_neuron_native_cold_label_v1_2026-10-14'
EP=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'


def load(p):
    with p.open() as f:return json.load(f)


def prepare():
    admission=load(METRICS/'label_admission.json');assert admission['label_accepted']
    diag=load(METRICS/'hotspot_diagnosis.json')
    assert diag['all_primary_metrics_exactly_reproduced_by_independent_Expat_domain']
    assert len(diag['sketch_top20'])==len(diag['native_top20'])==20
    cmd=load(NATIVE/'launch.json')['command'];graph=Path(cmd[cmd.index('--read_rr_graph')+1])
    bindings=closure([Path(__file__)])
    for p in [graph,EP,NATIVE/'output.route',*[MODEL/n for n in ['initial.json','sketch.json','receipt.json']]]:
        assert str(p) in admission['bindings'],('unbound old input',p)
        bindings[str(p)]=admission['bindings'][str(p)]
    for p in [METRICS/'label_admission.json',METRICS/'hotspot_diagnosis.json',METRICS/'prediction_metrics.json']:
        bindings[str(p)]=sha(p)
    assert sha(METRICS/'prediction_metrics.json')==diag['bindings'][str(METRICS/'prediction_metrics.json')]
    OUT.mkdir(exist_ok=False)
    (OUT/'protocol.json').write_text(json.dumps(dict(bindings=bindings,graph=str(graph),endpoint=str(EP),
        prepared_utc=datetime.now(timezone.utc).isoformat(),predicted_bins=diag['sketch_top20'],true_bins=diag['native_top20'],
        original_nodes=3593250,original_edges=39165143,connections=77106,NETs_per_round=50767,rounds=2,
        analysis_memory_limit_bytes=512*2**20,extra_margin_bytes=8*2**30,
        revalidate_all_inputs_before_and_after_analysis=True,post_label_diagnostic=True,
        primary_metrics_or_model_change_allowed=False,
        scope='All complete original records/events/native route traversed; attributed bins are exactly the frozen predicted and true top20, not a replacement evaluation subset. No causal improvement, new candidate, heldout, timing or hardware claim.'),indent=2)+'\n')
    print('PREPARED full-input top20 NET/transaction attribution',flush=True)


def run():
    resource.setrlimit(resource.RLIMIT_AS,(512*2**20,512*2**20));tick=time.perf_counter()
    protocol=load(OUT/'protocol.json');s=snapshot();reserve=0
    if s['model']['verified_live']:
        text=Path('/proc/1075109/status').read_text().splitlines()
        vms=int(next(line for line in text if line.startswith('VmSize:')).split()[1])*1024
        reserve=max(0,20*2**30-vms)
    elif not s['stages']['model']['terminal']['observed']:
        reserve=20*2**30
    free=s.get('shared_headroom_bytes',0)
    required=protocol['analysis_memory_limit_bytes']+protocol['extra_margin_bytes']+reserve
    admission=dict(checked_utc=datetime.now(timezone.utc).isoformat(),shared_headroom_bytes=free,
        remaining_live_model_reservation_bytes=reserve,analysis_limit_bytes=protocol['analysis_memory_limit_bytes'],
        extra_margin_bytes=protocol['extra_margin_bytes'],required_headroom_bytes=required,analysis_launched=free>=required)
    (OUT/'resource_admission_latest.json').write_text(json.dumps(admission,indent=2)+'\n')
    if free<required:
        print('NOT LAUNCHED shared memory admission',json.dumps(admission),flush=True);return
    assert not (OUT/'verification.json').exists()
    for p,h in protocol['bindings'].items():assert sha(p)==h,p
    rows={r['bin']:r for r in protocol['predicted_bins']+protocol['true_bins']}
    selected=domain(protocol['graph'],set(rows))
    assert selected['counts']==dict(nodes=protocol['original_nodes'],edges=protocol['original_edges'])
    for key,row in rows.items():assert selected['bin_capacities'][key]==row['capacity']
    print('DOMAIN PASS',len(selected['members']),'channels',len(selected['edge_sink']),'incoming edges',flush=True)
    initial,_,fanout,icount=model_owners(MODEL/'initial.json',selected)
    final,hot_connections,ffanout,fcount=model_owners(MODEL/'sketch.json',selected)
    assert icount==fcount==protocol['connections'] and fanout==ffanout and len(fanout)==protocol['NETs_per_round']
    selected_nets=set(initial)|set(final)
    names={int(k):v for k,v in object_members(EP,'net_names') if int(k) in selected_nets}
    assert set(names)==selected_nets and len(set(names.values()))==len(names)
    actual,native_headers=native_owners(NATIVE/'output.route',set(selected['members']))
    native_counts=incidences(actual,selected['members'])
    initial_counts={names[n]:c for n,c in incidences(initial,selected['members']).items()}
    final_counts={names[n]:c for n,c in incidences(final,selected['members']).items()}
    print('COMPLETE RECORDS/NATIVE UNIONS PASS',icount,fcount,native_headers,flush=True)
    wanted=set(final);events={};seen=defaultdict(set);all_status=defaultdict(Counter)
    for rnd,event in round_events(MODEL/'receipt.json'):
        net=event['net_id'];assert rnd in [0,1] and net in fanout and net not in seen[rnd]
        seen[rnd].add(net);all_status[rnd][event['status']]+=1
        if net in wanted:
            events[rnd,net]=dict(status=event['status'],old_epoch=event['old_epoch'],new_epoch=event['new_epoch'],
                primary_search_calls=event.get('primary_search_calls'),
                primary_failed_connection_count=len(event.get('primary_failed_connection_ids',[])),
                retained_hot_connection_count=len(set(event.get('retained_connection_ids',[]))&hot_connections[net]),
                fallback_status=event.get('fallback',{}).get('status'),
                prospective_overflow_delta=event.get('prospective_overflow_delta'),objective_guard=event.get('objective_guard'))
    assert set(seen)=={0,1} and all(seen[i]==set(fanout) for i in [0,1])
    summaries=[]
    for key,row in rows.items():
        totals=[sum(c.get(key,0) for c in counts.values()) for counts in [initial_counts,final_counts,native_counts]]
        for v,metric in zip(totals,['initial_utilization','sketch_utilization','native_utilization']):
            assert Fraction(str(row[metric]))*row['capacity']==v,(key,metric,v)
        by_status=Counter();contributors=[]
        for net in final:
            count=final_counts[names[net]].get(key,0)
            if not count:continue
            e=events[1,net];by_status[e['status']]+=count
            contributors.append(dict(net_id=net,name=names[net],fanout=fanout[net],
                predicted_channel_incidences=count,native_channel_incidences=native_counts.get(names[net],{}).get(key,0),
                round0=events[0,net],round1=e))
        assert sum(by_status.values())==totals[1]
        summaries.append(dict(row,initial_incidences=totals[0],final_incidences=totals[1],native_incidences=totals[2],
            final_incidences_by_round1_status=dict(by_status),
            final_model_only_NET_incidences=sum(c['predicted_channel_incidences'] for c in contributors if c['native_channel_incidences']==0),
            contributors=sorted(contributors,key=lambda c:(-c['predicted_channel_incidences'],c['net_id']))))
    predicted={r['bin'] for r in protocol['predicted_bins']}
    result=dict(bindings={**protocol['bindings'],str(OUT/'protocol.json'):sha(OUT/'protocol.json')},
        all_pass=True,all_original_connections_scanned_per_frame=icount,all_round_events_scanned={k:len(v) for k,v in seen.items()},
        all_round_status_counts={k:dict(v) for k,v in all_status.items()},complete_XML_nodes=selected['counts']['nodes'],
        complete_XML_edges=selected['counts']['edges'],selected_positive_channel_nodes=len(selected['members']),
        selected_bin_capacity_and_all_three_occupancy_vectors_exact=True,
        predicted_hotspot_components_sharing_physical_channel_nodes=components(predicted,selected['members']),
        original_segment_metadata=selected['segments'],bins=summaries,post_label_diagnostic=True,
        primary_metrics_unchanged=True,model_unchanged=True,promoted=False,
        seconds=time.perf_counter()-tick,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scope=protocol['scope'])
    for p,h in protocol['bindings'].items():assert sha(p)==h,p
    with (OUT/'verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','bins']},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','run']);args=parser.parse_args()
    globals()[args.stage]()
