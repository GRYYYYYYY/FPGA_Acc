"""Join audited selected trees with frozen exposed native risk owner pairs."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/mmc_cost_aware_selected_support_v1_2026-10-19'
    out.mkdir(exist_ok=False)
    dag=R/'experiments/mmc_missing_owner_DAG_diagnosis_v1_2026-10-19'
    dp=dag/'independent_verification_v1.json';d=json.loads(dp.read_text())
    assert d['status']=='ALL18_PAIR_COMPLETENESS_PARENT_KEY_DAG_MEMBERSHIP_AND_MODE_COUNTS_PASS'
    review=dag/'review.json';assert d['bindings'][str(review)]==sha(review)
    dr=json.loads(review.read_text())
    ap=R/'experiments/mmc_complete_static_criticality_audit_v1_2026-10-19/verification.json';a=json.loads(ap.read_text())
    assert a['status']=='ALL3_COMPLETE_SELECTED_PATHS_XML_BUDGETS_SINGLEPARENT_LEDGER_AND_ACCEPTED_GATE_REPLAY_PASS'
    bindings={str(p):sha(p) for p in [dp,review,ap,Path(__file__).resolve()]}
    protocol=dict(cases=['episode_01','episode_02','episode_03'],native_arm='zero',native_phase='final',
        domain='Only actual native NET/resource pairs in the archived positive-risk CHANNEL subset. Not all positive CHANNELs or all native routes.',
        question='Does the physically admitted static-cost selected tree contain native owners excluded by the min-raw/min-hop probability support?',
        scope='Retrospective selected-state coverage, not search reachable-set coverage, probability calibration, causal effect, complete quality or new prediction. Rejected counterfactual paths unavailable; no attribution to their contents.')
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    rows=[]
    for case in protocol['cases']:
        source=next(x for x in dr['rows'] if (x['case'],x['arm'],x['phase'])==(case,'zero','final'))
        pp=Path(source['per_pair']);assert dr['bindings'][str(pp)]==sha(pp)
        events=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19'/case/'events.jsonl'
        assert a['bindings'][str(events)]==sha(events)
        selected={}
        for line in events.open():
            e=json.loads(line);net=e['net_id'];assert net not in selected
            selected[net]=(set(e['chosen_owned']),e['decision'])
        assert len(selected)==55300
        counts=Counter();modes=defaultdict(Counter);decisions=defaultdict(Counter);seen=set()
        target=out/(case+'.pairs.jsonl')
        with target.open('x') as f:
            for line in pp.open():
                pair=json.loads(line);key=pair['net_id'],pair['node'];assert key not in seen;seen.add(key)
                owned,decision=selected[pair['net_id']];covered=pair['node'] in owned
                label=pair['support_stage']+'__'+('selected' if covered else 'absent')
                counts[label]+=1;modes[pair['model_mode']][label]+=1;decisions[decision][label]+=1
                f.write(json.dumps(dict(pair,selected_cost_tree_contains=covered,selected_decision=decision),separators=(',',':'))+'\n')
        assert len(seen)==source['actual_pairs']
        for stage,count in source['stage_counts'].items():assert counts[stage+'__selected']+counts[stage+'__absent']==count
        rows.append(dict(case=case,actual_pairs=len(seen),counts=dict(counts),by_model_mode={k:dict(v) for k,v in modes.items()},by_selection_decision={k:dict(v) for k,v in decisions.items()}))
        bindings.update({str(p):sha(p) for p in [pp,events,target]})
        print('COST_SELECTED_SUPPORT',case,dict(counts),flush=True)
    (out/'review.json').write_text(json.dumps(dict(status='ALL3_COST_SELECTED_SUPPORT_JOIN_PRODUCED',rows=rows,bindings=bindings,independent_join_verification_pending=True,scope=protocol['scope']),indent=2)+'\n')


if __name__=='__main__':main()
