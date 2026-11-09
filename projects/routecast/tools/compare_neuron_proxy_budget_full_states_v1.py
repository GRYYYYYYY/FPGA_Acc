"""Full admitted continue-after-rejection state comparison; no routing or metric selection."""
import datetime
import json
import resource
from collections import Counter, defaultdict
from pathlib import Path
import neuron_proxy_budget_trial_v2 as trial


def main():
    final=trial.OUT/'independent_final_admission_v1.json'
    metric=trial.OUT/'metrics/verification.json'
    assert final.exists() and metric.exists(), 'Full closed admission/all8 metrics required before diagnostics'
    chain=trial.R/'experiments/neuron_proxy_budget_full_chain_v2_2026-10-17'
    assert (chain/'terminal.json').exists(), 'Full chain terminal required'
    closed=trial.load(chain/'terminal.json')
    assert closed['exit_status']==0 and closed['full_model_all3audits_closed_admission_and_all8_metrics_completed'] is True and trial.gone(chain)
    admission=trial.load(final);quality=trial.load(metric)
    assert admission['all_pass'] and quality['all_pass'] and quality['independently_checked_metric_sets']==8
    trial.check(admission['bindings']);trial.check(quality['bindings'])
    free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free>=20*2**30
    resource.setrlimit(resource.RLIMIT_AS,(2*2**30,2*2**30))
    paths=[trial.BASELINE/'model/sketch.json',trial.OUT/'model/sketch.json']
    bindings={str(p):trial.sha(p) for p in [Path(__file__),final,metric,*paths]}
    states=[trial.load(p) for p in paths]
    for state in states:
        assert state['completed_connections']==state['required_connections']==len(state['records'])==77106
        assert state['eligible_for_legal_route_commit'] is False
    assert states[0]['graph_sha256']==states[1]['graph_sha256']
    indexes=[{r['connection_id']:r for r in s['records']} for s in states]
    assert all(set(index)==set(range(77106)) for index in indexes)
    pins_path=trial.CRITICALITY/'initial_connection_criticalities.json'
    bindings[str(pins_path)]=trial.sha(pins_path)
    import math,struct
    from fractions import Fraction
    criticalities={x['connection_id']:Fraction(struct.unpack('<f',struct.pack('<f',float(x['criticality_float32_text'])))[0]) for x in trial.load(pins_path)}
    assert set(criticalities)==set(range(77106))
    nets=defaultdict(list);changed=Counter();delay_changes=Counter();allowance_use=Counter();allowance_CIDs=[]
    for cid in range(77106):
        a,b=(index[cid] for index in indexes)
        assert {k:v for k,v in a.items() if k not in ['answer','budget_integer']}=={k:v for k,v in b.items() if k not in ['answer','budget_integer']}
        assert a['answer']['delay']<=a['budget_integer']
        expected=a['budget_integer']+math.ceil((1-criticalities[cid])*a['floor_integer'])
        assert b['budget_integer']==expected and b['answer']['delay']<=expected
        assert a['answer']['status']==b['answer']['status']=='FOUND'
        net=a['net_id'];nets[net].append(cid)
        if b['answer']['delay']>a['budget_integer']:
            allowance_use[net]+=1;allowance_CIDs.append(cid)
        changed[net]+=a['answer']['physical_edge_ids']!=b['answer']['physical_edge_ids']
        delay_changes[net]+=a['answer']['delay']!=b['answer']['delay']
    assert len(nets)==50767
    groups={key:Counter() for key in ('fanout1','fanout2_to15','fanout16_plus')}
    rows=[]
    for net,cids in sorted(nets.items()):
        fanout=len(cids);group=groups['fanout1' if fanout==1 else 'fanout2_to15' if fanout<16 else 'fanout16_plus']
        group['nets']+=1;group['connections']+=fanout;group['changed_connections']+=changed[net]
        group['changed_delay_connections']+=delay_changes[net]
        group['final_paths_using_extra_budget']+=allowance_use[net]
        group['nets_using_extra_budget']+=allowance_use[net]>0
        union_a={edge for cid in cids for edge in indexes[0][cid]['answer']['physical_edge_ids']}
        union_b={edge for cid in cids for edge in indexes[1][cid]['answer']['physical_edge_ids']}
        union_changed=union_a!=union_b
        group['nets_with_changed_connection_path']+=changed[net]>0
        group['nets_with_changed_edge_union']+=union_changed
        if changed[net] or delay_changes[net] or allowance_use[net]:
            rows.append(dict(net_id=net,fanout=fanout,changed_connections=changed[net],changed_delay_connections=delay_changes[net],
                final_paths_using_extra_budget=allowance_use[net],edge_union_changed=union_changed,removed_union_edges=len(union_a-union_b),added_union_edges=len(union_b-union_a)))
    assert sum(g['connections'] for g in groups.values())==77106
    assert sum(g['nets'] for g in groups.values())==50767
    ledgers=[{int(n):v for n,v in s['ledger'].items()} for s in states]
    histogram=Counter();increased=decreased=0
    for n in set(ledgers[0])|set(ledgers[1]):
        delta=ledgers[1].get(n,0)-ledgers[0].get(n,0)
        if delta:
            histogram[delta]+=1
            increased+=max(0,delta);decreased+=max(0,-delta)
    trial.check(bindings)
    out=trial.R/'experiments/neuron_proxy_budget_full_state_comparison_v1_2026-10-17';out.mkdir()
    trial.write(out/'verification.json',dict(all_pass=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bindings=bindings,
        all_original_connections=77106,all_original_NETs=50767,metadata_floors_source_sink_unchanged_budgets_independently_recomputed=True,final_paths_using_extra_budget_CIDs=allowance_CIDs,
        groups={k:dict(v) for k,v in groups.items()},changed_NET_rows=rows,
        physical_node_occupancy_delta_histogram=dict(histogram),increased_node_NET_memberships=increased,decreased_node_NET_memberships=decreased,
        final_overflow_units=[s['overflow_units'] for s in states],strict_unseen=False,promoted=False,
        scope='Complete admitted new-budget versus continuation final-state comparison on exposed neuron development case. New path raw greater than original budget establishes actual allowance use, not same-snapshot recovery or native timing feasibility. Physical-node ledger includes all resource types, not only channels. Edge unions are directed physical edge IDs; changed paths and changed NET unions differ. No native routing equivalence, proof of sole error cause, or paired continuous workflow benefit.'))
    print(json.dumps(dict(groups={k:dict(v) for k,v in groups.items()},changed_NETs=len(rows))))


if __name__=='__main__':main()
