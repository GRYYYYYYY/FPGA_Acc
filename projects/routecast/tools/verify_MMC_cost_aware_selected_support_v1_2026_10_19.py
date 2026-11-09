"""Verify join by per-resource owner inversion of already audited selected states."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/mmc_cost_aware_selected_support_v1_2026-10-19'
    rp=out/'review.json';review=json.loads(rp.read_text())
    assert all(sha(p)==h for p,h in review['bindings'].items())
    rows=[]
    for row in review['rows']:
        case=row['case'];source=R/'experiments/mmc_missing_owner_DAG_diagnosis_v1_2026-10-19'/f'{case}_zero_final.jsonl'
        native={}
        for line in source.open():
            p=json.loads(line);key=p['node'],p['net_id'];assert key not in native;native[key]=p
        relevant={node for node,net in native};owners=defaultdict(set);decisions={}
        events=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19'/case/'events.jsonl'
        for line in events.open():
            e=json.loads(line);decisions[e['net_id']]=e['decision']
            for node in e['chosen_owned']:
                if node in relevant:owners[node].add(e['net_id'])
        counts=Counter();by_mode=defaultdict(Counter);by_decision=defaultdict(Counter);seen=set()
        for line in (out/(case+'.pairs.jsonl')).open():
            p=json.loads(line);key=p['node'],p['net_id'];assert key in native and key not in seen;seen.add(key)
            original=native[key]
            assert all(p[k]==v for k,v in original.items())
            covered=p['net_id'] in owners[p['node']]
            assert p['selected_cost_tree_contains']==covered and p['selected_decision']==decisions[p['net_id']]
            label=p['support_stage']+'__'+('selected' if covered else 'absent')
            counts[label]+=1;by_mode[p['model_mode']][label]+=1;by_decision[p['selected_decision']][label]+=1
        assert seen==set(native) and len(seen)==row['actual_pairs'] and dict(counts)==row['counts']
        assert {k:dict(v) for k,v in by_mode.items()}==row['by_model_mode']
        assert {k:dict(v) for k,v in by_decision.items()}==row['by_selection_decision']
        rows.append(dict(case=case,verified_pairs=len(seen)))
        print('COST_SELECTED_RESOURCE_OWNER_INVERSION_PASS',case,len(seen),flush=True)
    assert len(rows)==3
    with (out/'independent_verification_v1.json').open('x') as f:
        json.dump(dict(status='ALL3_SELECTED_SUPPORT_PAIRS_AND_MODE_DECISION_COUNTS_INDEPENDENT_JOIN_PASS',rows=rows,bindings={str(p):sha(p) for p in [rp,Path(__file__).resolve()]},scope='Independent complete join arithmetic over inherited admitted states. No new physical path replay, search-space coverage or new predictor claim.'),f,indent=2)


if __name__=='__main__':main()
