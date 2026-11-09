"""Compare two preexisting input-derived budgets against certified native delays."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/mmc_current_budget_scope_v1_2026-10-19';out.mkdir(exist_ok=False)
    prior=R/'experiments/mmc_native_path_floor_gap_diagnosis_v1_2026-10-19';pp=prior/'review.json';p=json.loads(pp.read_text())
    vp=prior/'independent_verification_v1.json';v=json.loads(vp.read_text());assert v['status']=='ALL9_1040148_NATIVE_PARENT_CHAINS_XML_COSTS_AND_ARCHIVED_FLOOR_JOINS_PASS' and v['bindings'][str(pp)]==sha(pp)
    bindings={str(x):sha(x) for x in [pp,vp,Path(__file__).resolve()]};rows=[]
    for i in range(1,4):
        case=f'episode_{i:02d}';root=R/'experiments/mmc_prospective_swap_initializers_v1_2026-10-19'/case
        ip=root/'initial_independent_verification_v1.json';iv=json.loads(ip.read_text());assert iv['status']=='pass' and iv['all115572V2budgets_matched']
        initial=root/'raw_min/initial.json';assert iv['bindings'][str(initial)]==sha(initial)
        anchored={x['connection_id']:x for x in json.loads(initial.read_text())['records']}
        static=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19'/case/'records.jsonl'
        static_proof=R/'experiments/mmc_complete_static_criticality_audit_v1_2026-10-19/verification.json';sp=json.loads(static_proof.read_text());assert sp['bindings'][str(static)]==sha(static)
        minimum={x['connection_id']:x for x in map(json.loads,static.open())}
        native=prior/(case+'_zero.jsonl');assert p['bindings'][str(native)]==sha(native)
        counts=Counter();changed_budget=0;old_larger=0;seen=set();grouped=Counter()
        for x in map(json.loads,native.open()):
            cid=x['connection_id'];assert cid not in seen;seen.add(cid);a=anchored[cid];b=minimum[cid]
            assert all(a[k]==b[k]==x[k] for k in ['net_id','source','sink'])
            raw=x['native_cost_hops'][0];ab=a['budget_integer'];bb=b['budget_integer']
            assert bb==max(10**9,(3*b['floor_integer']+1)//2)
            assert ab>=bb
            changed_budget+=int(ab!=bb);old_larger+=int(ab>bb)
            key=('static_pass' if raw<=bb else 'static_fail')+'__'+('anchored_pass' if raw<=ab else 'anchored_fail')
            counts[key]+=1;grouped[a['net_id'],key]+=1
        assert seen==set(anchored)==set(minimum)==set(range(115572))
        rows.append(dict(case=case,connections=len(seen),different_input_budgets=changed_budget,anchored_larger=old_larger,native_budget_partition=dict(counts)))
        bindings.update({str(x):sha(x) for x in [ip,initial,static,static_proof,native]})
        print('CURRENT_BUDGET_SCOPE',case,dict(counts),'different',changed_budget,flush=True)
    (out/'audit.json').write_text(json.dumps(dict(status='ALL3_EXISTING_STATIC_AND_ANCHORED_BUDGET_DOMAINS_AND_NATIVE_PARTITIONS_CHECKED',rows=rows,bindings=bindings,
        scope='Retrospective exact comparison of two already archived input-only budget policies. No budget selected/tuned using target labels, no new candidate or implied gain; feasibility under complete global resource constraints remains separate.'),indent=2)+'\n')


if __name__=='__main__':main()
