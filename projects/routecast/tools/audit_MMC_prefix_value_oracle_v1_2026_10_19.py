"""Posthoc scalar-feature information bound; never emits deployable predictions."""
import pathlib,json,hashlib,sys,itertools,random
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from prefix_value_capture_bound_v1 import ceiling
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def tied_capture(scores,truth,k):
    # Independent enumeration of the score boundary rather than group-density allocation.
    order=sorted(range(len(scores)),key=lambda i:-scores[i]);boundary=scores[order[k-1]];above=[i for i,v in enumerate(scores) if v>boundary];equal=[i for i,v in enumerate(scores) if v==boundary]
    return (Fraction(sum(truth[i] for i in above))+Fraction((k-len(above))*sum(truth[i] for i in equal),len(equal)))/sum(truth)
def main():
    out=R/'experiments/mmc_prefix_value_oracle_v1_2026-10-19';out.mkdir();checks=0
    for seed in range(40):
        rng=random.Random(seed);g=rng.randrange(1,5);prefix=[i for i in range(g) for _ in range(rng.randrange(1,4))];truth=[rng.randrange(5) for _ in prefix]
        if not sum(truth):truth[0]=1
        for k in range(1,len(prefix)+1):
            bound=ceiling(prefix,truth,k)['capture'];best=Fraction(-1)
            for assignment in itertools.product(range(g),repeat=g):
                value=tied_capture([assignment[i] for i in prefix],truth,k);assert value<=bound;best=max(best,value);checks+=1
            assert best==bound
    prior=R/'experiments/mmc_prefix_future_pressure_baselines_v1_2026-10-18';proof=json.loads((prior/'verification.json').read_text());assert proof['independent_metric_vectors']==36;result=json.loads((prior/'results.json').read_text());domain=json.loads((prior/'channel_domain.json').read_text());split=R/'experiments/mmc_prefix_future_pressure_split_v1_2026-10-18';bindings={str(p):sha(p) for p in [pathlib.Path(__file__).resolve(),R/'tools/prefix_value_capture_bound_v1.py',prior/'verification.json',prior/'results.json',prior/'channel_domain.json']};rows=[]
    for row in result['cases']:
        case,policy=row['case'],row['policy'];predfile=prior/f'{case}_{policy}_prediction.json';assert sha(predfile)==row['prediction_sha256'];prefix=json.loads(predfile.read_text())['prediction'];targetfile=split/f'{case}_{policy}/targets.json';targets=json.loads(targetfile.read_text())['targets'];bindings[str(predfile)]=sha(predfile);bindings[str(targetfile)]=sha(targetfile);metrics={}
        for name,data in targets.items():
            truth=[data.get(str(n),0) for n in domain];b=ceiling(prefix,truth,len(domain)//20);actual=Fraction(row['metrics'][name]['prefix_overflow']['tie_averaged_mass_capture']);assert actual<=b['capture'];metrics[name]=dict(oracle_capture=str(b['capture']),oracle_capture_float=float(b['capture']),prefix_capture=str(actual),gap=float(b['capture']-actual),observable_groups=len(b['groups']),zero_feature_group_size=b['groups'].get(0,[0,0])[0],zero_feature_future_mass=b['groups'].get(0,[0,0])[1],total_future_mass=b['total_mass'],oracle_allocation=b['allocation'])
        rows.append(dict(case=case,policy=policy,targets=metrics));print(case,policy,metrics['sum_checkpoint_overflow_units']['oracle_capture_float'],flush=True)
    v=dict(status='scalar_prefix_value_oracle_bound_verified_on_exposed_data',bindings=bindings,exhaustive_small_score_assignments=checks,cases=rows,derivation='For each observable value group with size n and future mass m, uniform selection inside that group has mass rate m/n. Any scalar-only score allocates K slots among groups. Sorting those rates maximizes even the fractional allocation relaxation; that allocation is attained by a group-constant oracle score with at most one partial boundary group.',scope='Label-dependent oracle diagnosis only, not a predictor or training result. Covers scores using only each resource own scalar first-checkpoint overflow with uniform boundary ties. Does not bound graph/context/spatial features, resource-specific identities, or the original fixed-ID cold quality gates. All cases are exposed one-family partial-seed data.',accepted_gain=False,strict_unseen_admitted=False)
    (out/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print('small score assignments checked',checks,flush=True)
if __name__=='__main__':main()
