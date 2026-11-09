"""Complete closed control/candidate query coverage and within-snapshot continuation."""
import json
import resource
from collections import Counter,defaultdict
from itertools import zip_longest
from pathlib import Path
import neuron_continue_primary_trial_v1 as trial
from compare_complete_receipt_events_stream_v1 import round_items


def event_counts(event,expected,continued):
    searched=event['primary_search_connection_ids'];kept=event['retained_connection_ids'];a=set(searched);b=set(kept)
    assert len(a)==len(searched)==event['primary_search_calls'] and len(b)==len(kept) and not a&b and a|b<=expected
    result=Counter(events=1,queries=len(expected),searched=len(a),retained=len(b),unsearched=len(expected-a-b),NET_committed=event['status']=='COMMITTED',fallback_events='fallback' in event)
    if continued:
        assert a|b==expected
        rows=event['primary_rejected_expansions'];positions={cid:i for i,cid in enumerate(searched)};rejected=[x['connection_id'] for x in rows]
        assert len(rejected)==len(set(rejected)) and all(cid in a for cid in rejected)
        assert [positions[cid] for cid in rejected]==sorted(positions[cid] for cid in rejected)
        result['rejected_expansions']=len(rejected)
        if rejected:
            first=positions[rejected[0]];extra=len(searched)-first-1;later_rejections=len(rejected)-1
            assert extra>=later_rejections
            result['events_with_rejection']=1;result['queries_after_first_rejection']=extra;result['successful_expansions_after_first_rejection']=extra-later_rejections
    return result


def main():
    # Direct counterexamples verify that extra searches are not all counted as successes.
    e=dict(primary_search_connection_ids=[0,1,2,3],retained_connection_ids=[],primary_search_calls=4,status='COMMITTED',primary_rejected_expansions=[dict(connection_id=0),dict(connection_id=2)])
    c=event_counts(e,set(range(4)),True);assert c['queries_after_first_rejection']==3 and c['successful_expansions_after_first_rejection']==2
    e=dict(primary_search_connection_ids=[0],retained_connection_ids=[],primary_search_calls=1,status='COMMITTED');assert event_counts(e,set(range(4)),False)['unsearched']==3
    admission_path=trial.OUT/'independent_final_admission_v1.json';metric_path=trial.OUT/'metrics/verification.json'
    assert admission_path.exists() and metric_path.exists(), 'Complete independent admission/all8 metrics required'
    chain=trial.R/'experiments/neuron_continue_primary_full_chain_v1_2026-10-17'
    assert (chain/'terminal.json').exists(), 'Full chain terminal required'
    closed=trial.load(chain/'terminal.json')
    assert closed['exit_status']==0 and closed['full_model_all3audits_closed_admission_and_all8_metrics_completed'] is True and trial.gone(chain)
    admission=trial.load(admission_path);metric=trial.load(metric_path)
    assert admission['all_pass'] and admission['all_primary_coverage_and_isolated_rejection_audits_pass']
    assert metric['all_pass'] and metric['independently_checked_metric_sets']==8
    trial.check(admission['bindings']);trial.check(metric['bindings'])
    free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert free>=9*2**30
    resource.setrlimit(resource.RLIMIT_AS,(512*2**20,512*2**20))
    cids=defaultdict(set)
    for q in trial.load(trial.ENDPOINT)['connections']:cids[q['net_id']].add(q['connection_id'])
    paths=[trial.BASELINE/'model/receipt.json',trial.OUT/'model/receipt.json']
    bindings={str(p):trial.sha(p) for p in (Path(__file__),admission_path,metric_path,trial.ENDPOINT,*paths)}
    summary={method:defaultdict(Counter) for method in ('control','continued')};selected=[];seen=defaultdict(set);sentinel=object()
    for old,new in zip_longest(round_items(paths[0]),round_items(paths[1]),fillvalue=sentinel):
        assert old is not sentinel and new is not sentinel and old[:2]==new[:2]
        kind,index,item=old;other=new[2]
        if kind=='event':
            net=item['net_id'];assert net==other['net_id'] and net not in seen[index];seen[index].add(net)
            a=event_counts(item,cids[net],False);b=event_counts(other,cids[net],True)
            summary['control'][index].update(a);summary['continued'][index].update(b)
            if net in (56,1768,21348,21505):selected.append(dict(round_index=index,net_id=net,control=dict(a),continued=dict(b)))
        else:
            assert set(item['affected_nets'])==set(other['affected_nets'])==set(cids)==seen[index]
            assert len(item['affected_nets'])==len(other['affected_nets'])==50767
    assert set(seen)=={0,1} and sum(map(len,seen.values()))==101534
    assert sum(v['unsearched'] for v in summary['continued'].values())==0
    trial.check(bindings)
    out=trial.R/'experiments/neuron_continue_primary_coverage_comparison_v1_2026-10-17';out.mkdir()
    result=dict(all_pass=True,bindings=bindings,full_NET_events=101534,all_original_queries_each_round=77106,
        per_round={m:{str(k):dict(v) for k,v in rows.items()} for m,rows in summary.items()},selected_NET_rows=selected,
        candidate_unsearched_connections=0,scope='Complete admitted receipt accounting. Extra calls after first rejection are a within-candidate-snapshot counterfactual to its own early stop; full control and candidate trajectories/retained eligibility differ. Successful primary expansions are not necessarily committed NET transactions, native QoR, or hotspot gains. All8 metrics reported separately.',promoted=False)
    trial.write(out/'verification.json',result)
    print(json.dumps(result['per_round'],indent=2))


if __name__=='__main__':main()
