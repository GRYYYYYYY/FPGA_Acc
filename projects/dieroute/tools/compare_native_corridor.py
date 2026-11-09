#!/usr/bin/env python3
"""Compare frozen native corridor development runs; no physical QoR inference."""
import argparse
from collections import Counter,defaultdict
import csv
import json
import mmap
from pathlib import Path
import shutil
import struct
import time
from run_native_case import sha256


def die_path_census(run, command):
    """Classify physical die walks independently of the C++ policy filter."""
    graph=Path(command[1]);footprint=Path(command[3]);paths=defaultdict(list)
    with (run/'route/paths.csv').open() as f:
        for r in csv.DictReader(f):
            if r['repeat']=='0':paths[int(r['task'])].append({k:int(v) for k,v in r.items()})
    with (run/'route/selection.csv').open() as f:selection={int(r['task']):r for r in csv.DictReader(f)}
    walks=Counter();reentry=[];incidental=[];crossings=Counter();incidental_resources=set()
    with (graph/'nodes.bin').open('rb') as nf,(graph/'pips.bin').open('rb') as pf,(footprint/'tasks.bin').open('rb') as tf,\
         mmap.mmap(nf.fileno(),0,access=mmap.ACCESS_READ) as nodes,mmap.mmap(pf.fileno(),0,access=mmap.ACCESS_READ) as pips,mmap.mmap(tf.fileno(),0,access=mmap.ACCESS_READ) as tasks:
        def member(n):return struct.unpack_from('<I',nodes,n*64+20)[0]
        for task,sel in selection.items():
            source_die,sink_die=struct.unpack_from('<II',tasks,task*32+16)
            path=paths.get(task,[]);sequence=[source_die];previous=int(sel['source']);internal=[];last_pip_die=None
            for step,p in enumerate(path):
                assert p['step']==step and p['source']==previous
                record=struct.unpack_from('<8I',pips,(p['pip_key']>>1)*32);die=record[6]
                assert record[0]==p['pip_key']>>1
                assert tuple(record[1:3][::-1] if p['pip_key']&1 else record[1:3])==(p['source'],p['destination'])
                assert member(p['source'])&member(p['destination'])&(1<<die)
                if sequence[-1]!=die:
                    assert member(previous)&(1<<sequence[-1]) and member(previous)&(1<<die)
                    crossings[(sequence[-1],die)]+=1;sequence.append(die)
                if last_pip_die is not None and member(previous)&(member(previous)-1) and last_pip_die==die:
                    internal.append(previous);incidental_resources.add(previous)
                previous=p['destination'];last_pip_die=die
            assert previous==int(sel['sink'])
            if sequence[-1]!=sink_die:
                assert member(previous)&(1<<sequence[-1]) and member(previous)&(1<<sink_die)
                crossings[(sequence[-1],sink_die)]+=1;sequence.append(sink_die)
            key='>'.join(map(str,sequence));walks[key]+=1
            if len(set(sequence))!=len(sequence):reentry.append(task)
            if internal:incidental.append(task)
    return dict(paths=len(selection),die_walk_histogram=dict(walks),paths_with_die_reentry=reentry,
                paths_with_incidental_internal_boundaries=incidental,unique_incidental_boundary_nodes=sorted(incidental_resources),
                directed_transition_occurrences={f'{a}>{b}':v for (a,b),v in crossings.items()},
                scope='Final source-to-sink paths, including designated endpoint SLR transitions. Occurrences shared by multiple sinks are counted per path; these are not distinct SLL occupancy counts.')


def main():
    if not __debug__: raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    plan=json.loads(a.plan.read_text());out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source_hashes={}
    for name in (Path(__file__).name,'run_native_case.py'):
        source=Path(__file__).with_name(name);source_hashes[name]=sha256(source);shutil.copy2(source,out/name)
    inputs={str(a.plan.resolve()):sha256(a.plan)};results={};manifests={};core=None
    def merge(values):
        for path,digest in values.items():
            assert path not in inputs or inputs[path]==digest,path
            inputs[path]=digest
    for label,case in plan['cases'].items():
        run=Path(case['run']).resolve();mp=run/'manifest.json';m=json.loads(mp.read_text());manifests[label]=m
        assert m['status']=='passed' and m['inputs_unchanged'] and m['electrical_model_converged'] and int(m['command'][11])==5
        signature=m['command'][1:7]+m['command'][8:12]
        if core is None:core=signature
        assert signature==core
        inputs[str(mp)]=sha256(mp)
        for name,digest in m['artifacts'].items():inputs[str(run/name)]=digest
        ap=Path(case['cohort_audit']).resolve()/'audit.json';au=json.loads(ap.read_text());inputs[str(ap)]=sha256(ap)
        assert au['passed'] and au['inputs_unchanged'] and au['electrical_model_converged_repeats']==5 and au['inputs'][str(mp)]==sha256(mp)
        merge(au['inputs'])
        protocol=None
        if 'protocol_audit' in case:
            pp=Path(case['protocol_audit']).resolve()/'audit.json';protocol=json.loads(pp.read_text());inputs[str(pp)]=sha256(pp)
            assert protocol['passed'] and protocol['authority_reconstructed'] and protocol['complete_candidate_costs_verified'] and protocol['inputs'][str(mp)]==sha256(mp)
            merge(protocol['inputs'])
        with (run/'route/iterations.csv').open() as f:its=[r for r in csv.DictReader(f) if r['repeat']=='0']
        with (run/'route/trees.csv').open() as f:trees=[r for r in csv.DictReader(f) if r['repeat']=='0']
        with (run/'route/shadow_metrics.csv').open() as f:shadow=[r for r in csv.DictReader(f) if r['repeat']=='0'][0]
        by_net=Counter();sll=Counter();sll_by_net=defaultdict(list);seen=set();graph=Path(m['command'][1])
        gp=graph.parent/'manifest.json';gm=json.loads(gp.read_text());merge({str(gp):sha256(gp),str(graph/'intents.csv'):gm['artifacts']['graph/intents.csv']})
        with (graph/'intents.csv').open() as f:laguna={r['name']:int(r['id']) for r in csv.DictReader(f)}['NODE_LAGUNA_DATA']
        with (graph/'nodes.bin').open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as nodes:
            for r in trees:
                n=int(r['node']);assert n not in seen;seen.add(n)
                by_net[int(r['net'])]+=int(r['parent'])!=0xffffffff
                mask=struct.unpack_from('<I',nodes,n*64+20)[0];intent=struct.unpack_from('<I',nodes,n*64+28)[0]
                if mask&(mask-1) and intent==laguna:sll[mask]+=1;sll_by_net[int(r['net'])].append(n)
        values=dict(tree_pips=sum(by_net.values()),net_pips=dict(sorted(by_net.items())),net_sll_nodes={net:sll_by_net[net] for net in sorted(by_net)},selected_sll=dict(sll),iterations=len(its),overuse_by_epoch=[int(r['overused_nodes']) for r in its],
                    **{k:sum(int(r[k]) for r in its) for k in ('expanded','edge_visits','quotient_expanded','quotient_edge_visits')},
                    shadow_replays=int(shadow['replays']),logical_deliveries=int(shadow['logical_deliveries']),
                    complete_routing_and_five_repeats_verified=True)
        values['physical_die_path_census']=die_path_census(run,m['command'])
        if protocol:
            values['corridor_metrics']={k:v//5 for k,v in protocol['metrics'].items()}
            assert all(v%5==0 for v in protocol['metrics'].values())
            values['better_reentry_candidates']=protocol['better_reentry_candidates']//5
            values['better_portal_candidates']=protocol.get('better_portal_candidates',0)//5
            # Only accepted invocations: discard stale speculative candidates
            # from these diagnostics, while total work still includes replays.
            with (run/'route/corridor_runs.csv').open() as f:
                calls=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(f) if r['repeat']=='0']
            accepted={}
            for call in calls:accepted[call['search']]=call['replay']
            recorded=bool(calls and 'joint_expanded' in calls[0])
            phase_fields=('joint_expanded','joint_edge_visits','local_expanded','local_edge_visits','flat_expanded','flat_edge_visits')
            values['search_work_partition']=dict(recorded=recorded,**{k:values['corridor_metrics'][k] if recorded else None for k in phase_fields})
            if recorded:
                assert values['expanded']==sum(values['search_work_partition'][k+'_expanded'] for k in ('joint','local','flat'))
                assert values['edge_visits']==sum(values['search_work_partition'][k+'_edge_visits'] for k in ('joint','local','flat'))
            schedule=protocol.get('schedule',{})
            values['controller_schedule']=dict(verified=schedule.get('controller_schedule_verified',False))
            if schedule.get('controller_schedule_verified'):
                for field in ('passes','rescue_transitions','accepted_budget_deferrals','searches'):
                    assert schedule[field]%5==0;values['controller_schedule'][field]=schedule[field]//5
            fallback_calls=[c for c in calls if c['flat_searches'] and accepted[c['search']]==c['replay']]
            recovered=[]
            for failed in fallback_calls:
                if failed['status']!=0 and any(c['search']>failed['search'] and c['task']==failed['task'] and c['iteration']==failed['iteration'] and c['status']==0 and not c['flat_searches'] and accepted[c['search']]==c['replay'] for c in calls):
                    recovered.append(failed['task'])
            values['accepted_fallback_diagnostic']=dict(invocations=len(fallback_calls),successful=sum(c['status']==0 for c in fallback_calls),
                final_status_histogram=dict(Counter(c['status'] for c in fallback_calls)),later_completed_constrained_in_same_epoch=sorted(set(recovered)),
                scope='Final status of the whole invocation after fallback; does not identify the earlier constrained-discovery failure status.')
            choices=defaultdict(list);attempt_status=Counter()
            with (run/'route/corridor_trace.csv').open() as f:
                for raw in csv.DictReader(f):
                    r={k:int(v) for k,v in raw.items()}
                    if r['repeat']==0 and r['stage']==0 and 'search_status' in r:attempt_status[r['search_status']]+=1
                    if r['repeat']==0 and r['stage']==0 and r['completed'] and accepted[r['search']]==r['replay']:
                        choices[r['search']].append(r)
            improvements=ties=cost_saved=0;histogram=Counter()
            for choices_at_call in choices.values():
                first=choices_at_call[0];chosen=[r for r in choices_at_call if r['selected']];assert len(chosen)==1
                selected=chosen[0];histogram[selected['attempt']]+=1
                assert selected['cost']<=first['cost']
                improvements+=selected['cost']<first['cost'];cost_saved+=first['cost']-selected['cost']
                ties+=selected['attempt']!=first['attempt'] and selected['cost']==first['cost']
            values['accepted_candidate_diagnostic']=dict(invocations=len(choices),strict_cost_improvements=improvements,
                equal_cost_tie_changes=ties,cost_saved_vs_first_complete=cost_saved,selected_attempt_histogram=dict(histogram),
                scope='Per accepted invocation at its current tree/occupancy; excludes stale invocations. These are incremental algorithm costs, not physical delay, wirelength or globally optimized final-tree savings.')
            values['attempt_status_histogram_including_replays']=dict(attempt_status) if recorded else None
        results[label]=values
    baseline=results[plan['baseline']]
    for label,r in results.items():
        r['tree_pip_delta_vs_flat_percent']=100*(r['tree_pips']/baseline['tree_pips']-1)
        r['expanded_delta_vs_flat_percent']=100*(r['expanded']/baseline['expanded']-1)
        r['per_net_pip_delta_vs_flat']={str(net):r['net_pips'][net]-v for net,v in baseline['net_pips'].items()}
        r['changed_sll_net_ids']=[net for net in baseline['net_pips'] if r['net_sll_nodes'][net]!=baseline['net_sll_nodes'][net]]
        r['larger_trees_with_same_sll_ids']=[net for net,v in baseline['net_pips'].items() if r['net_pips'][net]>v and r['net_sll_nodes'][net]==baseline['net_sll_nodes'][net]]
    identities=[]
    for left,right in plan['required_equal_routes']:
        for name in ('selection.csv','trees.csv','usage.csv','paths.csv','connections.csv'):
            assert manifests[left]['artifacts']['route/'+name]==manifests[right]['artifacts']['route/'+name],(left,right,name)
        identities.append([left,right])
    clamp=[]
    for old,new in plan['quotient_radius_pairs']:
        for name in ('corridor_runs.csv','corridor_trace.csv','corridor_paths.csv','corridor_candidates.csv','shadow_trace.csv','shadow_reads.csv','shadow_final.csv','shadow_metrics.csv'):
            assert manifests[old]['artifacts']['route/'+name]==manifests[new]['artifacts']['route/'+name],name
        before,after=results[old],results[new]
        assert after['expanded']==before['expanded'] and after['edge_visits']==before['edge_visits']
        assert after['quotient_expanded']<=before['quotient_expanded'] and after['quotient_edge_visits']<=before['quotient_edge_visits']
        clamp.append(dict(before=old,after=new,complete_corridor_and_shadow_journals_equal=True,
                          quotient_expanded_reduction_percent=100*(1-after['quotient_expanded']/before['quotient_expanded']),
                          quotient_edge_visits_reduction_percent=100*(1-after['quotient_edge_visits']/before['quotient_edge_visits'])))
    for path,digest in inputs.items():assert sha256(path)==digest,path
    for name,digest in source_hashes.items():assert sha256(out/name)==sha256(Path(__file__).with_name(name))==digest
    observed_equal=[label for label,m in manifests.items() if all(m['artifacts']['route/'+name]==manifests[plan['baseline']]['artifacts']['route/'+name] for name in ('selection.csv','trees.csv','usage.csv','paths.csv','connections.csv'))]
    preserved_work=[]
    for new,new_m in manifests.items():
        if len(new_m['command'])<19 or new_m['command'][18]!='1':continue
        for old,old_m in manifests.items():
            if len(old_m['command'])<18 or (len(old_m['command'])>=19 and old_m['command'][18]!='0'):continue
            if old_m['command'][12:18]!=new_m['command'][12:18] or old_m['source_sha256']!=new_m['source_sha256']:continue
            equal=all(old_m['artifacts']['route/'+f]==new_m['artifacts']['route/'+f] for f in ('corridor_trace.csv','corridor_candidates.csv','corridor_paths.csv'))
            check=dict(immediate=old,deferred=new,complete_constrained_journals_equal=equal)
            if equal:
                before,after=results[old],results[new]
                for suffix in ('expanded','edge_visits'):
                    assert all(before['search_work_partition'][kind+'_'+suffix]==after['search_work_partition'][kind+'_'+suffix] for kind in ('joint','local'))
                    saved=before[suffix]-after[suffix]
                    assert saved==before['search_work_partition']['flat_'+suffix]-after['search_work_partition']['flat_'+suffix]
                    check['removed_flat_'+suffix]=saved
            preserved_work.append(check)
    result=dict(schema='dieroute.native_corridor_comparison.v1',passed=True,inputs=inputs,inputs_unchanged=True,finished_ns=time.time_ns(),
                per_repeat=results,exact_route_equalities=identities,quotient_radius_comparisons=clamp,auditor_sources=source_hashes,
                observed_routes_equal_to_baseline=observed_equal,
                observed_constrained_work_comparisons=preserved_work,
                board_result=False,native_design_legal=None,joint_qor_passed=False,
                scope='Fixed 70-net development cohort. Electrical legality and protocol verified; PIP counts are not physical wirelength, expansion counts are not latency, and concurrently run processes do not establish CPU speedup. No new native DCP/STA signoff.')
    (out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    with (out/'summary.csv').open('w') as f:
        fields=['case','tree_pips','iterations','expanded','edge_visits','quotient_expanded','quotient_edge_visits','shadow_replays','logical_deliveries']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for name,r in results.items():writer.writerow(dict(case=name,**{k:r[k] for k in fields[1:]}))
    print(json.dumps(dict(passed=True,cases=len(results),quotient_radius_comparisons=clamp)))


if __name__=='__main__':main()
