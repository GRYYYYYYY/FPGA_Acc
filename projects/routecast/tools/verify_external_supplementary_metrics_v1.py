"""Independent tie-block integer-rank recomputation of all feasible case metrics."""
import json,math
from collections import Counter
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19'
def correlation(a,b):
    def rank2(values):
        counts=Counter(values);position=0;ranks={}
        for value in sorted(counts):ranks[value]=2*position+counts[value]-1;position+=counts[value]
        return [ranks[v] for v in values]
    x,y=rank2(a),rank2(b);n=len(x);sx,sy=sum(x),sum(y);cov=n*sum(u*v for u,v in zip(x,y))-sx*sy
    vx=n*sum(u*u for u in x)-sx*sx;vy=n*sum(v*v for v in y)-sy*sy
    return None if not vx or not vy else cov/math.sqrt(vx*vy)
def main():
    terminal=D/'execution/terminal.json';assert json.loads(terminal.read_text())['status']=='ALL_STAGES_TERMINAL'
    domain=R/'experiments/prospective_external_family_quality_domains_v2_2026-10-19/w160';resources=[json.loads(s) for s in (domain/'resources.jsonl').read_text().splitlines()];bin_rows=json.loads((domain/'spatial_bins.json').read_text());capacities={tuple(r['key']):r['capacity'] for r in bin_rows};domain_proof=json.loads((domain/'verification.json').read_text());bindings={**domain_proof['bindings'],str(terminal):sha(terminal),str(Path(__file__).resolve()):sha(__file__)};rows=[]
    for episode in range(1,4):
        case=f'w160/episode_{episode:02d}';comparison=D/'predictions'/case/'comparison.json';c=json.loads(comparison.read_text());spec_path=D/'specifications'/case/'comparison_spec.json';spec=json.loads(spec_path.read_text());bindings.update(c['bindings']);bindings[str(comparison)]=sha(comparison)
        label=json.loads(Path(spec['label_physical_audit']).read_text());ledgers={'truth':{int(n):v for n,v in label['node_occupancy'].items()}}
        for method,path in [('previous_native',spec['source_frame']),*[(k,v['frame']) for k,v in spec['predictions'].items()]]:ledgers[method]={int(n):v for n,v in json.loads(Path(path).read_text())['ledger'].items()}
        vectors={}
        for method,ledger in ledgers.items():
            concrete={};bins=Counter()
            for r in resources:
                n=r['id'];value=ledger.get(n,0);concrete[n]=Fraction(value,r['capacity'])
                for key in r['bins']:bins[tuple(key)]+=value
            vectors[method]={'resource':concrete,'spatial':{k:Fraction(bins[k],v) for k,v in capacities.items()}}
        for method in ('previous_native','raw_min_on','native_retained_on'):
            for scope,k in [('resource',domain_proof['resource_k']),('spatial',domain_proof['spatial_k'])]:
                a=vectors[method][scope];b=vectors['truth'][scope];ids=sorted(b)
                predicted=set(sorted(ids,key=lambda n:(-a[n],n))[:k]);truth=set(sorted(ids,key=lambda n:(-b[n],n))[:k]);hits=len(predicted&truth);rho=correlation([a[n] for n in ids],[b[n] for n in ids]);observed=c['metrics'][method][scope]
                assert observed['top_k_hits']==hits and observed['universe_size']==len(ids) and observed['k']==k
                assert (rho is None and observed['spearman'] is None) or abs(rho-observed['spearman'])<1e-12
                rows.append(dict(case=case,method=method,scope=scope,spearman=rho,top_k_hits=hits,k=k))
        # The top-K counter alone independently refutes each case's gate vs old.
        assert c['metrics']['native_retained_on']['resource']['top_k_hits']<c['metrics']['previous_native']['resource']['top_k_hits']
        assert c['metrics']['native_retained_on']['spatial']['top_k_hits']<c['metrics']['previous_native']['spatial']['top_k_hits']
    assert all(sha(p)==h for p,h in bindings.items())
    (D/'independent_metrics_verification_v1.json').write_text(json.dumps(dict(status='ALL18_METRIC_VECTORS_INDEPENDENT_INTEGER_TIE_RANKS_AND_EXACT_TOPK_VERIFIED',bindings=bindings,rows=rows,all3_cases_refuted_by_both_exact_topK_counters=True,scope='Independent metric arithmetic over graph-domain records previously verified against XML. Full45,584 resource and2208bin domains retained. No unseen admission, native utility or complete time gain.'),indent=2)+'\n');print('ALL18_INDEPENDENT_METRIC_VECTORS_PASS')
if __name__=='__main__':main()
