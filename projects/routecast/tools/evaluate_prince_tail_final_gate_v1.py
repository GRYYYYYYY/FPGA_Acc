"""Prespecified native h1 primary phase-to-final target transfer check."""
import json
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from expected_channel_forecast_vectors_v1 import vectors
from external_forecast_metrics_v1 import vectors as physical,metrics,gate
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'prince_tail_final_gate_v1_2026-10-20';S=E/'prince_paired_exposure_features_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
    protocol=load(D/'protocol.json')
    for p,h in protocol['binding'].items():assert sha(p)==h
    source=load(S/'tail_projection_evaluation_v1.json');features=load(S/'frozen_features.json');distributions={}
    for row in source['distributions']:
        if row['mode']=='native':distributions[row['case'],row['horizon'],tuple(row['key'])]=row['distribution']
    rows=[];bindings={str(p):sha(p) for p in [D/'protocol.json',Path(__file__),R/'tools/external_forecast_metrics_v1.py',R/'tools/expected_channel_forecast_vectors_v1.py']}
    for row in features['rows']:
        case=row['case']
        if row['status']=='NO_READY_EVENT':rows.append(dict(case=case,status='NO_READY_EVENT',primary_pass=False));continue
        fp=Path(row['features']);ready=list(map(json.loads,fp.open()));sp=E/'prince_feedback_quality_v1_2026-10-20'/case/'specification.json';spec=load(sp);lp=Path(spec['label_physical_audit']);truth={int(n):v for n,v in load(lp)['node_occupancy'].items()};folder=E/'prince_quality_domains_v1_2026-10-20'/case.split('/')[0];rp=folder/'resources.jsonl';bp=folder/'spatial_bins.json';mp=folder/'verification.json';resources=list(map(json.loads,rp.open()));bins=load(bp);meta=load(mp);cp=sp.parent/'comparison.json';original=load(cp);labels=physical(resources,bins,truth,meta['graph_nodes'],truth=True);results={}
        out=D/case;out.mkdir(parents=True)
        for h in [1,2]:
            pred={}
            for r in ready:
                key=('native',h,r['occupancy'],r['acc_bits'],r['Q']);d=distributions[case,h,key];s=sum((F(*p) for o,p in d.items() if int(o)>0),F(0));assert 0<=s<=1;pred[r['id']]=s
            scorep=out/f'h{h}_scores.jsonl'
            with scorep.open('x') as f:
                for node,s in sorted(pred.items()):f.write(json.dumps(dict(id=node,numerator=s.numerator,denominator=s.denominator))+'\n')
            ms=metrics(vectors(resources,bins,pred,meta['graph_nodes']),labels,meta['resource_k'],meta['spatial_k']);checks={c:gate(ms,original['metrics'][c]) for c in ['previous_native','raw_min_on']};results[str(h)]=dict(metrics=ms,checks=checks,pass_both_controls=all(c['pass_primary_gate'] for c in checks.values()),score_file=str(scorep));bindings[str(scorep)]=sha(scorep)
        for p in [fp,sp,lp,rp,bp,mp,cp]:bindings[str(p)]=sha(p)
        rows.append(dict(case=case,status='SCORED',primary_pass=results['1']['pass_both_controls'],horizons=results));print('FINAL_TRANSFER',case,results['1']['pass_both_controls'],results['2']['pass_both_controls'],flush=True)
    out=dict(status='ORIGINAL_FINAL_GATE_TRANSFER_SCORED_PENDING_INDEPENDENT_AUDIT',rows=rows,full9_gate=False,primary_available_passes=sum(r['primary_pass'] for r in rows),required_cases=9,bindings=bindings)
    with (D/'verification.json').open('x') as f:json.dump(out,f,indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator));f.write('\n')
if __name__=='__main__':main()
