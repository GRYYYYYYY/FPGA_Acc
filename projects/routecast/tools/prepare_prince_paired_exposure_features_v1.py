"""Freeze ready-only exposure/density features, without phase-response label reads."""
import json
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from pre_route_endpoints import sha

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'experiments'
D = E / 'prince_paired_exposure_features_v1_2026-10-20'
S = E / 'prince_paired_cost_state_v1_2026-10-20'
Q = E / 'prince_causal_query_frontier_v1_2026-10-20'
N = E / 'prince_connection_query_trial_v1_2026-10-20'


def load(p):
    return json.loads(p.read_text())


def main():
    D.mkdir(exist_ok=False)
    protocol = dict(status='FEATURE_DESIGN_FROZEN_BEFORE_NEW_FIT',
        features=dict(occupancy='Ready integer global CHANNEL occupancy.',
                      acc_bits='Exact ready binary32 history word.',
                      E='floor(log2(1+number of distinct NETs querying this node during ready iteration));integer bit_length minus1,zero if unobserved. Observed cost paths only.',
                      Q='Quartile of exact mean leave-self-out occupied fraction in existing spatial bins;min(3,floor(4*density)).'),
        candidates=['pooled', 'stock', 'stockE', 'stockQ', 'stockEQ'],
        comparison='Same original whole-episode folds,mode/horizon conditioning,one persistence pseudo-observation and pooled fallback as frozen response baseline. No feature threshold tuning or candidate union.',
        evaluation='Add training-prevalence and zero-event references;event Brier and fixed top5percent resource event precision/recall (ascending node ID ties),calibration,occupancy/positive/excess proper scores. Auxiliary transient labels only;original final-label gates remain separate.',
        provenance='Require query-run native ready RR/NET owners/boxes and mapping byte parity with paired native source before importing ready query exposure. No future query rows or future phase labels read.',
        limits='Exposed development;6 ready prefixes,not24 independent arms. No native utility admission.',
        bindings={str(p):sha(p) for p in [S/'frozen_inputs.json',Q/'frozen_inputs.json',Path(__file__)]})
    (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    bindings = dict(protocol['bindings'])
    query = {r['case']:r for r in load(Q/'frozen_inputs.json')['rows']}
    rows = []
    comparisons = 0
    for base in load(S/'frozen_inputs.json')['rows']:
        case = base['case']
        if base['status'] == 'NO_READY_EVENT':
            rows.append(dict(case=case,status='NO_READY_EVENT'))
            continue
        t = base['ready_iteration']
        src = N/case/'capture'
        native = E/'prince_cost_advance_ablation_trial_v1_2026-10-20'/case/'native'
        for rel in ['NET_mapping.tsv', f'boundary/iteration_{t}.bin',
                    f'boundary/boxes_{t}.bin',f'owners/owners_{t}.bin']:
            a,b = src/rel,native/rel
            assert a.read_bytes() == b.read_bytes(), (case,rel)
            bindings[str(a)],bindings[str(b)] = sha(a),sha(b)
            comparisons += 1
        q = query[case]
        assert q['ready_iteration'] == t
        exposure = defaultdict(set)
        qp = Path(q['paths'][str(t)])
        assert sha(qp) == load(Q/'frozen_inputs.json')['bindings'][str(qp)]
        for r in map(json.loads,qp.open()):
            assert r['iteration'] == t
            exposure[r['node']].add(r['net'])
        ready = {r['id']:r for r in map(json.loads,Path(base['feature_file']).open())}
        rp = E/'prince_quality_domains_v1_2026-10-20'/case.split('/')[0]/'resources.jsonl'
        resources = list(map(json.loads,rp.open()))
        assert {r['id'] for r in resources} == set(ready)
        adj,occupied = defaultdict(set),defaultdict(int)
        for r in resources:
            for key in r['bins']:
                key = tuple(key)
                adj[key].add(r['id'])
                occupied[key] += ready[r['id']]['occupancy'] > 0
        out = D/case
        out.mkdir(parents=True)
        fp = out/'features.jsonl'
        with fp.open('x') as f:
            for r in resources:
                node = r['id']
                keys = [tuple(k) for k in r['bins']]
                assert keys and all(len(adj[k])>1 for k in keys)
                density = sum((Fraction(occupied[k]-int(ready[node]['occupancy']>0),len(adj[k])-1) for k in keys),Fraction())/len(keys)
                count = len(exposure[node])
                record = dict(id=node,occupancy=ready[node]['occupancy'],acc_bits=ready[node]['acc_bits'],
                              E=(count+1).bit_length()-1,Q=min(3,4*density.numerator//density.denominator),
                              distinct_query_NETs=count,peer_density=[density.numerator,density.denominator])
                f.write(json.dumps(record,separators=(',',':'))+'\n')
        for p in [fp,qp,rp,Path(base['feature_file'])]:bindings[str(p)]=sha(p)
        rows.append(dict(case=case,status='READY_ONLY_FEATURES_FROZEN',ready_iteration=t,
                         features=str(fp),resources=len(resources)))
        print('EXPOSURE_FEATURES_FROZEN',case,len(resources),flush=True)
    with (D/'frozen_features.json').open('x') as f:
        json.dump(dict(status='READY_ONLY_EXPOSURE_AND_DENSITY_FROZEN',rows=rows,
                       native_snapshot_byte_comparisons=comparisons,labels_read=False,bindings=bindings),f,indent=2)
        f.write('\n')


if __name__ == '__main__':
    main()
