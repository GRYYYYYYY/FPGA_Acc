"""Independent histogram metrics for six new control vectors and comparisons."""
import json
import pathlib
import xml.etree.ElementTree as ET
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
from verify_MMC_complete_static_criticality_metrics_v2_2026_10_19 import verify_metric

R = pathlib.Path(__file__).resolve().parents[1]


def main():
    out = R/'experiments/mmc_current_raw_min_on_cold_control_v1_2026-10-19'
    result = out/'results.json'
    d = json.loads(result.read_text())
    assert all(sha(p)==h for p,h in d['bindings'].items())
    graph = next(pathlib.Path(p) for p in d['bindings'] if p.endswith('rr_graph.xml'))
    channels, bins, stack = [], Counter(), []
    for event, e in ET.iterparse(graph,events=('start','end')):
        if event=='start':
            stack.append(e)
            continue
        if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
            if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
                loc, seg = e.find('loc'),e.find('segment')
                keys=[(int(loc.get('layer','0')),x,y,e.get('type'),int(seg.get('segment_id')) if seg is not None else -1) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)]
                cap=int(e.get('capacity'));channels.append((int(e.get('id')),cap,keys))
                for key in keys:bins[key]+=cap
            stack[-2].remove(e);e.clear()
        if e.tag=='rr_nodes':break
        stack.pop()
    assert len(channels)==258720 and len(bins)==17160
    prior_path=R/'experiments/mmc_complete_static_criticality_cold_quality_v1_2026-10-19/results.json'
    assert d['bindings'][str(prior_path)]==sha(prior_path)
    prior=json.loads(prior_path.read_text())
    decisions=[]
    for row in d['rows']:
        case=row['case']
        archived=next(x for x in prior['cases'] if x['case']==case)
        model=R/'experiments/mmc_current_raw_min_on_v1_2026-10-19'/case/'model/sketch.json'
        target=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case/'cold/physical_audit.json'
        p={int(n):Fraction(v) for n,v in json.loads(model.read_text())['ledger'].items()}
        t={int(n):Fraction(v) for n,v in json.loads(target.read_text())['node_occupancy'].items()}
        ps,ts=Counter(),Counter()
        concrete_p,concrete_t={},{}
        for n,cap,keys in channels:
            concrete_p[n]=p.get(n,Fraction())/cap;concrete_t[n]=t.get(n,Fraction())/cap
            for key in keys:ps[key]+=p.get(n,0);ts[key]+=t.get(n,0)
        verify_metric(concrete_p,concrete_t,12936,row['raw_min_on_metrics']['concrete'])
        verify_metric({k:Fraction(ps[k])/cap for k,cap in bins.items()},{k:Fraction(ts[k])/cap for k,cap in bins.items()},20,row['raw_min_on_metrics']['spatial'])
        for candidate,comp in row['comparisons'].items():
            flags=[]
            for c in comp['checks']:
                assert c['candidate']==archived['metrics'][candidate][c['scope']][c['metric']]
                ref=row['raw_min_on_metrics'][c['scope']][c['metric']]
                assert ref==c['control']
                eps=1e-12 if c['metric']=='spearman' else 0
                a,b=c['candidate']>=ref-eps,c['candidate']>ref+eps
                assert (a,b)==(c['nonregression'],c['strict']);flags.append((a,b))
            assert comp['raw_min_on_comparison_pass']==(all(a for a,b in flags) and any(b for a,b in flags))
        decisions.append(dict(case=case,comparisons={k:v['raw_min_on_comparison_pass'] for k,v in row['comparisons'].items()}))
        print('RAW_MIN_ON_INDEPENDENT_METRICS_PASS',case,flush=True)
    bindings={str(result):sha(result),str(pathlib.Path(__file__).resolve()):sha(__file__)}
    helper=R/'tools/verify_MMC_complete_static_criticality_metrics_v2_2026_10_19.py';bindings[str(helper)]=sha(helper)
    assert len(decisions)==3
    with (out/'independent_verification_v1.json').open('x') as f:
        json.dump(dict(status='ALL3_SIX_RAW_MIN_ON_METRIC_VECTORS_AND_COMPARISON_DECISIONS_PASS',metric_vectors=6,decisions=decisions,bindings=bindings),f,indent=2)


if __name__=='__main__':main()
