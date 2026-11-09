"""Independent tie-block integer-rank recomputation of all feasible case metrics."""
import json,math
from collections import Counter
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_zero_feedback_warm_v1_2026-10-19'
def correlation(a,b):
    def rank2(values):
        counts=Counter(values);position=0;ranks={}
        for value in sorted(counts):ranks[value]=2*position+counts[value]-1;position+=counts[value]
        return [ranks[v] for v in values]
    x,y=rank2(a),rank2(b);n=len(x);sx,sy=sum(x),sum(y);cov=n*sum(u*v for u,v in zip(x,y))-sx*sy
    vx=n*sum(u*u for u in x)-sx*sx;vy=n*sum(v*v for v in y)-sy*sy
    return None if not vx or not vy else cov/math.sqrt(vx*vy)
def main():
    terminal=D/'quality_summary.json';summary=json.loads(terminal.read_text());assert summary['status']=='ALL3_FIXED_ZERO_FEEDBACK_WARM_ORIGINAL_FORECAST_METRICS_EVALUATED';assert all(sha(p)==h for p,h in summary['bindings'].items());summary_rows={r['case']:r for r in summary['rows']};overlay_specs={r['case']:r for r in json.loads((D/'protocol.json').read_text())['cases']}
    domain=R/'experiments/prospective_external_family_quality_domains_v2_2026-10-19/w160';resources=[json.loads(s) for s in (domain/'resources.jsonl').read_text().splitlines()];bin_rows=json.loads((domain/'spatial_bins.json').read_text());capacities={tuple(r['key']):r['capacity'] for r in bin_rows};domain_proof=json.loads((domain/'verification.json').read_text());bindings={**domain_proof['bindings'],str(terminal):sha(terminal),str(Path(__file__).resolve()):sha(__file__)};rows=[]
    for episode in range(1,4):
        case=f'w160/episode_{episode:02d}';comparison=D/case/'comparison.json';c=json.loads(comparison.read_text());spec_path=D/case/'comparison_spec.json';spec=json.loads(spec_path.read_text());bindings.update(c['bindings']);bindings[str(comparison)]=sha(comparison)
        label=json.loads(Path(spec['label_physical_audit']).read_text());ledgers={'truth':{int(n):v for n,v in label['node_occupancy'].items()}}
        for method,path in [('previous_native',spec['source_frame']),*[(k,v['frame']) for k,v in spec['predictions'].items()]]:ledgers[method]={int(n):v for n,v in json.loads(Path(path).read_text())['ledger'].items()}
        original_path=Path(overlay_specs[case]['base_frame']);ledgers['original_candidate']={int(n):v for n,v in json.loads(original_path.read_text())['ledger'].items()};bindings[str(original_path)]=sha(original_path);vectors={};recomputed={}
        for method,ledger in ledgers.items():
            concrete={};bins=Counter()
            for r in resources:
                n=r['id'];value=ledger.get(n,0);concrete[n]=Fraction(value,r['capacity'])
                for key in r['bins']:bins[tuple(key)]+=value
            vectors[method]={'resource':concrete,'spatial':{k:Fraction(bins[k],v) for k,v in capacities.items()}}
        for method in ('previous_native','raw_min_on','native_retained_on','original_candidate'):
            recomputed[method]={}
            for scope,k in [('resource',domain_proof['resource_k']),('spatial',domain_proof['spatial_k'])]:
                a=vectors[method][scope];b=vectors['truth'][scope];ids=sorted(b)
                predicted=set(sorted(ids,key=lambda n:(-a[n],n))[:k]);truth=set(sorted(ids,key=lambda n:(-b[n],n))[:k]);hits=len(predicted&truth);rho=correlation([a[n] for n in ids],[b[n] for n in ids]);observed=summary_rows[case]['original_candidate_metrics'][scope] if method=='original_candidate' else c['metrics'][method][scope]
                assert observed['top_k_hits']==hits and observed['universe_size']==len(ids) and observed['k']==k
                assert (rho is None and observed['spearman'] is None) or abs(rho-observed['spearman'])<1e-12
                recomputed[method][scope]=dict(spearman=rho,top_k_hits=hits);rows.append(dict(case=case,method=method,scope=scope,spearman=rho,top_k_hits=hits,k=k))
        def decision(a,b):
            checks=[];strict=[]
            for scope in ['resource','spatial']:
                x,y=a[scope],b[scope];rx,ry=x['spearman'],y['spearman'];defined=rx is not None and ry is not None;checks.extend([defined and rx>=ry-1e-12,x['top_k_hits']>=y['top_k_hits']]);strict.extend([defined and rx>ry+1e-12,x['top_k_hits']>y['top_k_hits']])
            return all(checks) and any(strict)
        outcomes=[]
        for method in ['previous_native','raw_min_on']:
            passed=decision(recomputed['native_retained_on'],recomputed[method]);assert passed==c['checks'][method]['pass_primary_gate'];outcomes.append(passed)
        assert all(outcomes)==c['pass_case_gate']==summary_rows[case]['original_registered_case_gate']
        assert decision(recomputed['native_retained_on'],recomputed['original_candidate'])==summary_rows[case]['vs_original_candidate']['pass_primary_gate']
    assert summary['all9_availability_gate_pass'] is False and len(summary['unavailable_cases'])==6;assert summary['all3_original_case_gates_pass']==all(r['original_registered_case_gate'] for r in summary['rows'])
    assert all(sha(p)==h for p,h in bindings.items())
    (D/'independent_metrics_verification_v1.json').write_text(json.dumps(dict(status='ALL24_WARM_AND_CONTROL_METRIC_VECTORS_AND_GATE_DECISIONS_INDEPENDENTLY_VERIFIED',bindings=bindings,rows=rows,all3_original_case_gates_pass=all(r['original_registered_case_gate'] for r in summary['rows']),scope='Independent metric arithmetic over graph-domain records previously verified against XML. Full45,584 resource and2208bin domains retained. No unseen admission, native utility or complete time gain.'),indent=2)+'\n');print('ALL24_INDEPENDENT_METRIC_VECTORS_AND_GATES_PASS')
if __name__=='__main__':main()
