"""Original full cold metrics and independent precision-stability comparisons."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
from prediction_metrics import compare
from verify_MMC_complete_static_criticality_metrics_v2_2026_10_19 import verify_metric

R=Path(__file__).resolve().parents[1]
SCALE=10**12


def main():
    root=R/'experiments/mmc_joint_candidate_ensemble_v1_2026-10-19';rp=root/'receipt.json';vp=root/'independent_verification_v1.json';receipt=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['status']=='ALL3_ORIGINAL_BANKS_COMPLETE_RECURRENCES_HIGH_PRECISION_MARGINALS_AND_LEDGER_VERIFIED' and v['bindings'][str(rp)]==sha(rp)
    out=R/'experiments/mmc_joint_candidate_ensemble_quality_v1_2026-10-19';out.mkdir(exist_ok=False);original=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';inputs=json.loads(original.read_text());graph=Path(json.loads(Path(inputs['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);channels={};bins=Counter();caps={};stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
            n=int(e.get('id'));caps[n]=int(e.get('capacity'))
            if e.get('type') in ['CHANX','CHANY'] and caps[n]>0:
                loc,segment=e.find('loc'),e.find('segment');keys=[(int(loc.get('layer',0)),x,y,e.get('type'),int(segment.get('segment_id')) if segment is not None else -1) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)];channels[n]=keys
                for key in keys:bins[key]+=caps[n]
            stack[-2].remove(e);e.clear()
        if e.tag=='rr_nodes':break
        stack.pop()
    assert len(channels)==258720 and len(bins)==17160;pointpath=R/'experiments/mmc_resource_probability_quality_v1_2026-10-19/results.json';points=json.loads(pointpath.read_text());bindings={str(p):sha(p) for p in [rp,vp,original,graph,pointpath,Path(__file__).resolve()]};rows=[];vectors=0
    for item in inputs['cases']:
        case=item['case'];tp=Path(item['native_label']);assert inputs['bindings'][str(tp)]==sha(tp);truth={int(n):val for n,val in json.loads(tp.read_text())['node_occupancy'].items()};priorpath=Path(item['quality_reference_protocol']).with_name('comparison.json');assert points['bindings'][str(priorpath)]==sha(priorpath);prior=json.loads(priorpath.read_text());point=next(x for x in points['rows'] if (x['case'],x['arm'])==(case,points['primary_arm']))
        primarypath=root/case/'expected_ledger_scaled.json';secondarypath=root/case/'high_precision_expected_ledger_scaled.json';assert receipt['bindings'][str(primarypath)]==sha(primarypath) and v['bindings'][str(secondarypath)]==sha(secondarypath)
        primary={int(n):val for n,val in json.loads(primarypath.read_text()).items()};secondary={int(n):val for n,val in json.loads(secondarypath.read_text()).items()};all_results={};cache={}
        for name,ledger in [('float_primary',primary),('decimal60_check',secondary)]:
            if name=='decimal60_check' and ledger==primary:all_results[name]=dict(all_results['float_primary'],metrics_reused_by_identical_vectors=True);continue
            sp,st=Counter(),Counter()
            for n,keys in channels.items():
                for key in keys:sp[key]+=ledger.get(n,0);st[key]+=truth.get(n,0)
            p={n:Fraction(ledger.get(n,0),SCALE*caps[n]) for n in channels};t={n:Fraction(truth.get(n,0),caps[n]) for n in channels};ps={k:Fraction(sp[k],SCALE*cap) for k,cap in bins.items()};ts={k:Fraction(st[k],cap) for k,cap in bins.items()};metrics=dict(concrete=compare(p,t,12936),spatial=compare(ps,ts,20));verify_metric(p,t,12936,metrics['concrete']);verify_metric(ps,ts,20,metrics['spatial']);vectors+=2;comparisons={}
            for control in ['previous_native','raw_min_on','native_retained_on','all_NET_on','paired_MAP']:
                reference=point['metrics'] if control=='paired_MAP' else prior['metrics']['cold'][control];checks=[]
                for scope in ['concrete','spatial']:
                    for metric in ['spearman','precision_at_k']:
                        a,b=metrics[scope][metric],reference[scope][metric];eps=1e-12 if metric=='spearman' else 0;checks.append(dict(scope=scope,metric=metric,candidate=a,reference=b,nonregression=a>=b-eps,strict=a>b+eps))
                comparisons[control]=dict(checks=checks,pass_comparison=all(x['nonregression'] for x in checks) and any(x['strict'] for x in checks))
            all_results[name]=dict(metrics=metrics,comparisons=comparisons,full_mean_demand_overuse=Fraction(sum(max(0,val-SCALE*caps[n]) for n,val in ledger.items()),SCALE),eligible_for_legal_route_commit=False)
        stability={control:all_results['float_primary']['comparisons'][control]['pass_comparison']==all_results['decimal60_check']['comparisons'][control]['pass_comparison'] for control in all_results['float_primary']['comparisons']}
        rows.append(dict(case=case,precision_results=all_results,gate_decisions_stable=all(stability.values()),gate_stability=stability));bindings.update({str(p):sha(p) for p in [tp,priorpath,primarypath,secondarypath]});print('JOINT_ENSEMBLE_FULL_COLD_QUALITY',case,{k:x['pass_comparison'] for k,x in all_results['float_primary']['comparisons'].items()},'precision_stable',all(stability.values()),flush=True)
    result=out/'results.json'
    with result.open('x') as f:json.dump(dict(status='ALL3_JOINT_ENSEMBLE_AND_HIGH_PRECISION_COLD_METRICS_COMPUTED',rows=rows,bindings=bindings,numerical_metric_vectors=vectors,scope='Frozen joint complete-tree model, old exposed layouts. Mean overuse is not expected overuse; no global legalization, unseen-family, native utility or full-flow claim.'),f,indent=2,default=lambda x:str(x) if isinstance(x,Fraction) else None)
    helper=R/'tools/verify_MMC_complete_static_criticality_metrics_v2_2026_10_19.py'
    with (out/'independent_metric_verification_v1.json').open('x') as f:json.dump(dict(status='ALL_JOINT_ENSEMBLE_METRIC_VECTORS_AND_PRECISION_DECISION_STABILITY_CHECKED',metric_vectors=vectors,bindings={str(p):sha(p) for p in [result,helper,Path(__file__).resolve()]},scope='Independent histogram/topK/MAE routine in evaluation process; original and60digit ledgers scored where vectors differ.'),f,indent=2)


if __name__=='__main__':main()
