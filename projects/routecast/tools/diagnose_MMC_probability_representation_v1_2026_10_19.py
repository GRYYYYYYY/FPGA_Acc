"""Frozen marginal-score diagnostic; not a physical joint-route predictor."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
from prediction_metrics import compare
from verify_MMC_complete_static_criticality_metrics_v2_2026_10_19 import verify_metric

R=Path(__file__).resolve().parents[1]


def main():
    pp=R/'experiments/mmc_frozen_probability_representation_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());assert all(sha(p)==h for p,h in plan['bindings'].items());out=R/'experiments/mmc_probability_representation_v1_2026-10-19';out.mkdir(exist_ok=False)
    source=R/'experiments/mmc_resource_probability_development_v1_2026-10-19';pointpath=R/'experiments/mmc_resource_probability_quality_v1_2026-10-19/results.json';point=json.loads(pointpath.read_text());context=R/'experiments/mmc_resource_context_v1_2026-10-19';nodes=array('I');nodes.frombytes((context/'CHANNEL_ids.u32').read_bytes());assert len(nodes)==258720
    original=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';inputs=json.loads(original.read_text());graph=Path(json.loads(Path(inputs['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);channel={};bins=Counter();stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
            if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
                assert int(e.get('capacity'))==1;loc,seg=e.find('loc'),e.find('segment');keys=[(int(loc.get('layer',0)),x,y,e.get('type'),int(seg.get('segment_id')) if seg is not None else -1) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)];channel[int(e.get('id'))]=keys
                for key in keys:bins[key]+=1
            stack[-2].remove(e);e.clear()
        if e.tag=='rr_nodes':break
        stack.pop()
    assert list(nodes)==sorted(channel) and len(bins)==17160;bindings={str(p):sha(p) for p in [pp,pointpath,original,graph,context/'CHANNEL_ids.u32',Path(__file__).resolve()]};rows=[]
    for item in inputs['cases']:
        case=item['case'];tp=Path(item['native_label']);assert inputs['bindings'][str(tp)]==sha(tp);truth={int(n):v for n,v in json.loads(tp.read_text())['node_occupancy'].items()};assert all(truth.get(n,0) in [0,1] for n in nodes);priorpath=Path(item['quality_reference_protocol']).with_name('comparison.json');prior=json.loads(priorpath.read_text())
        for arm in [point['primary_arm'],point['ablation_arm']]:
            paired=next(x for x in point['rows'] if (x['case'],x['arm'])==(case,arm));probpath=source/case/arm/'probabilities.u32';assert plan['bindings'][str(probpath)]==sha(probpath);prob=array('I');prob.frombytes(probpath.read_bytes());assert len(prob)==len(nodes) and max(prob)<=10**6;p={n:Fraction(v,10**6) for n,v in zip(nodes,prob)};t={n:Fraction(truth.get(n,0)) for n in nodes};sp,st=Counter(),Counter()
            for n,keys in channel.items():
                for key in keys:sp[key]+=p[n];st[key]+=truth.get(n,0)
            spatial_p={k:Fraction(sp[k])/cap for k,cap in bins.items()};spatial_t={k:Fraction(st[k])/cap for k,cap in bins.items()};metrics=dict(concrete=compare(p,t,12936),spatial=compare(spatial_p,spatial_t,20));verify_metric(p,t,12936,metrics['concrete']);verify_metric(spatial_p,spatial_t,20,metrics['spatial'])
            # Two exact expressions independently check the binary Brier sum.
            brier=sum((p[n]-t[n])**2 for n in nodes)/len(nodes);integer_sum=sum((v-10**6*truth.get(n,0))**2 for n,v in zip(nodes,prob));assert brier==Fraction(integer_sum,len(nodes)*10**12)
            ledgerpath=source/case/arm/'ledger.json';ledger={int(n):v for n,v in json.loads(ledgerpath.read_text()).items()};point_squared=Fraction(sum((ledger.get(n,0)-truth.get(n,0))**2 for n in nodes),len(nodes));comparisons={}
            for control in ['previous_native','raw_min_on','native_retained_on','all_NET_on','paired_point']:
                ref=paired['metrics'] if control=='paired_point' else prior['metrics']['cold'][control];checks=[]
                for scope in ['concrete','spatial']:
                    for metric in ['spearman','precision_at_k']:
                        a,b=metrics[scope][metric],ref[scope][metric];eps=1e-12 if metric=='spearman' else 0;checks.append(dict(scope=scope,metric=metric,candidate=a,reference=b,nonregression=a>=b-eps,strict=a>b+eps))
                comparisons[control]=dict(checks=checks,pass_comparison=all(x['nonregression'] for x in checks) and any(x['strict'] for x in checks))
            rows.append(dict(case=case,arm=arm,marginal_metrics=metrics,paired_point_metrics=paired['metrics'],comparisons=comparisons,marginal_Brier=brier,point_squared_error=point_squared,probability_int_min=min(prob),probability_int_max=max(prob),probability_levels=len(set(prob)),total_expected_CHANNEL_occupancy=Fraction(sum(prob),10**6),native_occupied_CHANNELs=sum(truth.get(n,0) for n in nodes),diagnostic_only=True,has_complete_tree_joint_distribution_witness=False))
            bindings.update({str(p):sha(p) for p in [tp,priorpath,probpath,ledgerpath]});print('FROZEN_PROBABILITY_REPRESENTATION',case,arm,{k:v['pass_comparison'] for k,v in comparisons.items()},flush=True)
    result=out/'results.json'
    with result.open('x') as f:json.dump(dict(status='ALL6_FROZEN_MARGINAL_SCORE_DIAGNOSTICS_COMPUTED',rows=rows,bindings=bindings,scope=plan['interpretation']),f,indent=2,default=lambda x:str(x) if isinstance(x,Fraction) else None)
    helper=R/'tools/verify_MMC_complete_static_criticality_metrics_v2_2026_10_19.py'
    with (out/'independent_metric_verification_v1.json').open('x') as f:json.dump(dict(status='ALL12_MARGINAL_METRICS_AND_SIX_EXACT_BRIER_CROSSCHECKS_PASS',metric_vectors=12,Brier_checks=6,bindings={str(p):sha(p) for p in [result,helper,Path(__file__).resolve()]},scope='Independent histogram/rank/topK/MAE routine and exact integer Brier crosscheck in evaluation process; no physical joint-ensemble admission.'),f,indent=2)


if __name__=='__main__':main()
