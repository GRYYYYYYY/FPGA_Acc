"""Independent complete-row identity/budget accounting; no recost or predictor tuning."""
import json
import sys
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure


def main():
    root=R/'experiments/neuron_native_proxy_budget_compatibility_v3_2026-10-17';proof_path=root/'verification.json';proof=json.loads(proof_path.read_text());assert proof['all_pass'] and proof['all_original_CIDs_with_explicit_pin_identity']
    rows_path=root/'reference_rows.jsonl';assert sha(rows_path)==proof['bindings'][str(rows_path)]
    original=R/'experiments/neuron_quotient_astar_pipeline_v1_2026-10-17/model/initial.json'
    assert sha(original)==proof['bindings'][str(original)]
    records=json.loads(original.read_text())['records'];baseline={r['connection_id']:r for r in records};fanouts=Counter(r['net_id'] for r in records)
    crit=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/initial_connection_criticalities.json';assert sha(crit)==proof['bindings'][str(crit)]
    pins={r['connection_id']:(r['net'],r['local_sink_pin']) for r in json.loads(crit.read_text())}
    seen=set();per_net=defaultdict(Counter);groups=defaultdict(Counter);maximum=Fraction(0)
    with rows_path.open() as stream:
        for line in stream:
            r=json.loads(line);cid=r['connection_id'];assert type(cid) is int and cid in baseline and cid not in seen;seen.add(cid);old=baseline[cid]
            assert (r['net_id'],r['local_sink_pin'])==pins[cid]
            assert all(r[k]==old[k] for k in ('net_id','source','sink','floor_integer','budget_integer'))
            raw=r['native_path_additive_integer'];assert type(raw) is int and raw>=r['floor_integer']>=0
            violation=raw>r['budget_integer'];assert r['proxy_budget_feasible'] is (not violation)
            group='fanout1' if fanouts[r['net_id']]==1 else 'fanout2_to15' if fanouts[r['net_id']]<16 else 'fanout16_plus'
            for counter in (per_net[r['net_id']],groups[group]):
                counter['connections']+=1;counter['proxy_budget_violations']+=violation
            maximum=max(maximum,Fraction(raw,r['budget_integer']))
    assert seen==set(baseline)==set(range(77106))
    assert {str(n):dict(v) for n,v in per_net.items()}==proof['per_NET']
    assert sum(v['proxy_budget_violations'] for v in per_net.values())==proof['summary']['proxy_budget_violations']==2455
    assert str(maximum)==proof['maximum_exact_native_proxy_to_budget_ratio']
    bindings=closure([Path(__file__)]);bindings.update({str(p):sha(p) for p in (proof_path,rows_path,original,crit)})
    output=dict(all_pass=True,bindings=bindings,all_original_CIDs_independently_joined=True,all_original_budgets_and_explicit_native_pin_keys_match=True,
        fanout_groups={k:dict(v) for k,v in groups.items()},selected_NETs={str(n):dict(per_net[n]) for n in (56,1768,21348,21505)},
        total_connections=77106,total_proxy_violations=2455,maximum_exact_ratio=str(maximum),
        scope='Independent identity/row/comparison/count verification of full native-path additive-proxy diagnostic; graph/raw arithmetic is supplied by the prior exact physical context proof. Does not assert native STA violation, cause of hotspot failure, or benefit from relaxing budgets. Active candidate parameters unchanged.',promoted=False)
    p=root/'independent_accounting_v1.json'
    with p.open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('bindings','scope')},indent=2))


if __name__=='__main__':main()
