"""Complete known-reference constraint/criticality accounting; no budget fitting."""
import datetime
import json
import resource
import struct
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha


def main():
    free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert free>=9*2**30
    resource.setrlimit(resource.RLIMIT_AS,(512*2**20,512*2**20))
    ref=R/'experiments/neuron_native_proxy_budget_compatibility_v3_2026-10-17'
    proof_path=ref/'verification.json';account_path=ref/'independent_accounting_v1.json'
    proof=json.loads(proof_path.read_text());account=json.loads(account_path.read_text());assert proof['all_pass'] and account['all_pass']
    rows=ref/'reference_rows.jsonl';initial=R/'experiments/neuron_quotient_astar_pipeline_v1_2026-10-17/model/initial.json'
    criticality=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/initial_connection_criticalities.json'
    producer=R/'tools/run_design_scoped_quotient_astar_retained_tree_v2.py'
    inputs=[proof_path,account_path,rows,initial,criticality,producer]
    bindings=closure([Path(__file__)])
    for p in inputs:
        bindings[str(p)]=sha(p)
        for old in (proof,account):
            if str(p) in old['bindings']:assert bindings[str(p)]==old['bindings'][str(p)]
    original=json.loads(initial.read_text())['records'];old={r['connection_id']:r for r in original};fanout=Counter(r['net_id'] for r in original)
    criticalities={};pin_keys={}
    for row in json.loads(criticality.read_text()):
        cid=row['connection_id'];assert cid not in criticalities
        c=Fraction(struct.unpack('f',struct.pack('f',float(row['criticality_float32_text'])))[0]);assert 0<=c<=1
        assert (row['net'],row['source_rr'],row['target_rr'])==(old[cid]['net_id'],old[cid]['source'],old[cid]['sink'])
        criticalities[cid]=c;pin_keys[cid]=(row['net'],row['local_sink_pin'])
    assert set(criticalities)==set(old)==set(range(77106))
    denominator=max(c.denominator for c in criticalities.values());assert all(denominator%c.denominator==0 for c in criticalities.values())
    groups={};seen=set();minimum_budget=proof['scale']//10**9;integer_weight=integer_bad_weight=0
    def add(key,c,bad,floor,excess):
        g=groups.setdefault(key,dict(connections=0,violations=0,zero_floor_connections=0,sum_criticality=Fraction(0),violating_sum_criticality=Fraction(0),weighted_proxy_excess=Fraction(0),feasible_criticality_min=None,feasible_criticality_max=None,violating_criticality_min=None,violating_criticality_max=None))
        g['connections']+=1;g['violations']+=bad;g['zero_floor_connections']+=floor==0;g['sum_criticality']+=c;g['violating_sum_criticality']+=c if bad else 0;g['weighted_proxy_excess']+=c*excess
        prefix='violating' if bad else 'feasible'
        for suffix,op in (('min',min),('max',max)):
            name=prefix+'_criticality_'+suffix;g[name]=c if g[name] is None else op(g[name],c)
    with rows.open() as stream:
        for line in stream:
            row=json.loads(line);cid=row['connection_id'];assert cid in old and cid not in seen;seen.add(cid)
            o=old[cid];assert all(row[k]==o[k] for k in ('net_id','source','sink','floor_integer','budget_integer'))
            assert (row['net_id'],row['local_sink_pin'])==pin_keys[cid]
            floor,budget,raw=row['floor_integer'],row['budget_integer'],row['native_path_additive_integer'];ratio_budget=(3*floor+1)//2
            assert budget==max(minimum_budget,ratio_budget)>0 and raw>=floor>=0
            bad=raw>budget;assert row['proxy_budget_feasible'] is (not bad);c=criticalities[cid]
            unit=c.numerator*(denominator//c.denominator);integer_weight+=unit;integer_bad_weight+=unit if bad else 0
            branch='minimum_1ns_dominates' if minimum_budget>=ratio_budget else 'ratio_1p5_floor_dominates'
            f=fanout[row['net_id']];category='fanout1' if f==1 else 'fanout2_to15' if f<16 else 'fanout16_plus'
            keys=['all',category,branch,category+'/'+branch]
            if row['net_id'] in (56,1768,21348,21505):keys.append('NET'+str(row['net_id']))
            for key in keys:add(key,c,bad,floor,max(0,raw-budget))
    assert len(seen)==77106 and groups['all']['violations']==2455
    assert Fraction(integer_weight,denominator)==groups['all']['sum_criticality'] and Fraction(integer_bad_weight,denominator)==groups['all']['violating_sum_criticality']
    for key,counter in account['fanout_groups'].items():
        assert groups[key]['connections']==counter['connections'] and groups[key]['violations']==counter['proxy_budget_violations']
    result={}
    for key,g in groups.items():
        n,v=g['connections'],g['violations'];w,bw=g['sum_criticality'],g['violating_sum_criticality']
        result[key]={k:str(x) if isinstance(x,Fraction) else x for k,x in g.items()}
        result[key].update(violation_fraction_exact=str(Fraction(v,n)),criticality_weighted_violation_fraction_exact=str(bw/w) if w else None,
            mean_criticality_violation_exact=str(bw/v) if v else None,mean_criticality_feasible_exact=str((w-bw)/(n-v)) if n>v else None)
    assert all(sha(p)==h for p,h in bindings.items())
    out=R/'experiments/neuron_proxy_budget_criticality_v1_2026-10-17';out.mkdir()
    value=dict(all_pass=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bindings=bindings,all77106_CIDs_pin_keys_and_budget_formula_checked=True,
        exact_common_denominator_weight_crosscheck_pass=True,groups=result,resource_limit_bytes=512*2**20,
        scope='Complete post-label existing-reference accounting, algebraic budget branches and prior fanout categories only. Criticality association is confounded by NET/fanout and does not prove cause, native STA violation, calibrated slack, or benefit of a new budget policy. No fitted threshold, budget change, new labels/model or heldout claim.',promoted=False)
    (out/'verification.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('all','fanout16_plus','minimum_1ns_dominates','ratio_1p5_floor_dominates','NET56')},indent=2))


if __name__=='__main__':main()
