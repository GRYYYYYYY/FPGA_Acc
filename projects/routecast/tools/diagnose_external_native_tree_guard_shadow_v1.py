"""Retrospective native-tree admission at actual first-round event snapshots.
Target trees use labels; this is an oracle diagnosis, never a deployable model.
"""
import json
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from audit_structural_node_base_v1 import audit as rebuild_prices
from load_external_current_initial_timing_v1 import load as load_timing
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
    O=R/'experiments/prospective_external_family_native_guard_shadow_v1_2026-10-19';O.mkdir(exist_ok=False);first=read(D/'specifications/w160/episode_01/comparison_spec.json');graph,digest,nodes,fields,rc,unused=load_endpoints(first['endpoint']);caps=fields['capacities'];slots={eid:i for i,eid in enumerate(fields['edge_ids'])};dest=fields['dest_ranks'];span={}
    for n,node in enumerate(nodes):
        if node.get('type') in ('CHANX','CHANY'):
            loc=node.find('loc');span[n]=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1
    bindings={str(Path(__file__).resolve()):sha(__file__)};rows=[]
    def owned(recs):
        return {r['source'] for r in recs}|{dest[slots[e]] for r in recs for e in r['answer']['physical_edge_ids']}
    for episode in (1,2,3):
        case=f'w160/episode_{episode:02d}';specfile=D/'specifications'/case/'comparison_spec.json';spec=read(specfile);meta=read(spec['endpoint']);assert meta['graph_sha256']==digest;folder=Path(spec['predictions']['native_retained_on']['frame']).parent;protocol=read(folder/'protocol.json');receipt=read(folder/'receipt.json');audit_path=Path(spec['predictions']['native_retained_on']['proof']);audit=read(audit_path);assert audit['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];bindings.update(audit['bindings']);bindings[str(audit_path)]=sha(audit_path)
        warm=read(folder/'initial.json');events=receipt['rounds'][0]['events'];assert receipt['rounds'][0]['round_index']==0 and protocol['price_unit_integer']==rc.scale//(20*10**9)
        base=rebuild_prices(graph,protocol['structural_node_base_proof'],rc.scale);timing=load_timing(Path(protocol['criticality_input_proof']).parent,spec['endpoint']);criticality={cid:Fraction(r['criticality_numerator'],r['criticality_denominator']) for cid,r in timing.items()}
        route=Path(spec['label_physical_audit']).parent/'output.route';native_paths,native_rows,native_ledger=load_complete(route,meta,nodes,fields,rc);nr={r['connection_id']:r for r in native_rows};target=defaultdict(list);state=defaultdict(list)
        for r in warm['records']:state[r['net_id']].append(r)
        for q in meta['connections']:
            n=nr[q['connection_id']];target[q['net_id']].append(dict(q,answer=dict(physical_edge_ids=n['physical_edge_ids'],delay=n['delay_integer'])))
        ledger=Counter({int(n):v for n,v in warm['ledger'].items()});counts=Counter();details=[];old_score_checks=0
        def objective(recs,old_nodes):
            total=Fraction(0);users={}
            for r in recs:
                c=criticality[r['connection_id']];total+=c*r['answer']['delay']
                for eid in r['answer']['physical_edge_ids']:
                    n=dest[slots[eid]];users[n]=max(users.get(n,Fraction(0)),c)
            for n,c in users.items():
                other=ledger.get(n,0)-int(n in old_nodes)
                price=base[n]*(1+max(0,other-caps[n]+1))+protocol['price_unit_integer']*span.get(n,0)
                total+=(1-c)*price
            return total
        for event in events:
            net=event['net_id'];old=state[net];new=target[net];old_nodes=owned(old);new_nodes=owned(new);budgets={r['connection_id']:r['budget_integer'] for r in old};bad=[r['connection_id'] for r in new if r['answer']['delay']>budgets[r['connection_id']]]
            updates={n:ledger[n]-1 for n in old_nodes-new_nodes};updates.update({n:ledger[n]+1 for n in new_nodes-old_nodes});overflow_delta=sum(max(0,v-caps[n])-max(0,ledger[n]-caps[n]) for n,v in updates.items())
            old_score=objective(old,old_nodes);target_score=objective(new,old_nodes)
            if 'objective_guard' in event:
                assert old_score==Fraction(event['objective_guard']['old_score']);old_score_checks+=1
            if bad:classification='target_tree_outside_budget'
            elif overflow_delta>0 and target_score>old_score:classification='both_overflow_and_objective_reject'
            elif overflow_delta>0:classification='overflow_guard_reject_only'
            elif target_score>old_score:classification='objective_guard_reject_only'
            else:classification='target_tree_passes_both_guards'
            counts[classification]+=1;details.append(dict(net_id=net,classification=classification,native_budget_violation_CIDs=bad,prospective_overflow_delta=overflow_delta,objective_delta=str(target_score-old_score),actual_event_status=event['status']))
            if event['status']=='COMMITTED':
                committed=event['records'];committed_nodes=owned(committed)
                for n in old_nodes-committed_nodes:
                    ledger[n]-=1
                    if not ledger[n]:del ledger[n]
                for n in committed_nodes-old_nodes:ledger[n]+=1
                state[net]=committed
        round_state=read(receipt['rounds'][0]['state_file']);assert dict(ledger)=={int(n):v for n,v in round_state['ledger'].items()};assert sorted([r for rs in state.values() for r in rs],key=lambda r:r['connection_id'])==round_state['records'];assert len(events)==len(state)==5919
        warm_events=read(folder.parent/'warm/native_retained/initializer_events.json');fallbacks=sum(e['whole_NET_fallback'] for e in warm_events);assert fallbacks==0
        row=dict(case=case,first_round_NET_events=len(events),independent_actual_old_objective_checks=old_score_checks,classifications=dict(counts),warm_whole_NET_fallbacks=fallbacks,warm_retained_connections=sum(len(e['retained_connection_ids']) for e in warm_events));rows.append(row)
        p=O/f'episode_{episode:02d}_NETs.json';p.write_text(json.dumps(details,separators=(',',':'))+'\n')
        for path in [p,specfile,Path(spec['label_proof']),route,folder/'receipt.json',folder.parent/'warm/native_retained/initializer_events.json']:bindings[str(path)]=sha(path)
        print('NATIVE_TARGET_GUARD_SHADOW',json.dumps(row),flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (O/'verification.json').write_text(json.dumps(dict(status='ALL17757_FIRST_ROUND_NATIVE_TARGET_TREE_SHADOW_ADMISSIONS_REPLAYED',bindings=bindings,rows=rows,scope='Label-using retrospective oracle at exact serial first-round event snapshots; old objective crosschecked wherever recorded and final round state/ledger exactly reproduced. Native tree budget/overflow/objective barriers are snapshot-specific; does not prove all alternatives impossible, global multiNET irreducibility, causal forecast loss, a deployable algorithm or promotion.'),indent=2)+'\n')
if __name__=='__main__':main()
