"""Original full-domain quality gates for fixed owner-context model."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
from prediction_metrics import compare
from verify_MMC_complete_static_criticality_metrics_v2_2026_10_19 import verify_metric
R=Path(__file__).resolve().parents[1]
def main():
    source=R/'experiments/mmc_owner_frequency_development_v1_2026-10-19';rp=source/'receipt.json';proof=source/'independent_verification_v1.json';v=json.loads(proof.read_text());assert v['status']=='ALL3_OWNER_FREQUENCY_HISTOGRAMS_INTEGER_ROUNDING_SCATTER_FLOWCUT_AND_LEDGER_PASS' and v['bindings'][str(rp)]==sha(rp);receipt=json.loads(rp.read_text());assert all(sha(p)==h for p,h in receipt['bindings'].items())
    out=R/'experiments/mmc_owner_frequency_quality_v1_2026-10-19';out.mkdir(exist_ok=False)
    original=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';inputs=json.loads(original.read_text());graph=Path(json.loads(Path(inputs['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);channels={};bins=Counter();caps={};stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
            n=int(e.get('id'));cap=int(e.get('capacity'));caps[n]=cap
            if e.get('type') in ['CHANX','CHANY'] and cap>0:
                loc,segment=e.find('loc'),e.find('segment');keys=[(int(loc.get('layer',0)),x,y,e.get('type'),int(segment.get('segment_id')) if segment is not None else -1) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)];channels[n]=keys
                for k in keys:bins[k]+=cap
            stack[-2].remove(e);e.clear()
        if e.tag=='rr_nodes':break
        stack.pop()
    assert len(channels)==258720 and len(bins)==17160
    frozenpath=R/'experiments/mmc_resource_probability_quality_v1_2026-10-19/results.json';frozen=json.loads(frozenpath.read_text());bindings={str(p):sha(p) for p in [rp,proof,original,graph,frozenpath,Path(__file__).resolve()]};rows=[]
    for item in inputs['cases']:
        case=item['case'];lp=source/case/'ledger.json';ledger={int(n):val for n,val in json.loads(lp.read_text()).items()};label=Path(item['native_label']);assert inputs['bindings'][str(label)]==sha(label);truth={int(n):val for n,val in json.loads(label.read_text())['node_occupancy'].items()};quality=Path(item['quality_reference_protocol']).with_name('comparison.json');assert frozen['bindings'][str(quality)]==sha(quality);prior=json.loads(quality.read_text());control216=next(x for x in frozen['rows'] if x['case']==case and x['arm']==frozen['primary_arm']);sp,st=Counter(),Counter()
        for n,keys in channels.items():
            for k in keys:sp[k]+=ledger.get(n,0);st[k]+=truth.get(n,0)
        vectors={'concrete':({n:Fraction(ledger.get(n,0),caps[n]) for n in channels},{n:Fraction(truth.get(n,0),caps[n]) for n in channels},12936),'spatial':({k:Fraction(sp[k],cap) for k,cap in bins.items()},{k:Fraction(st[k],cap) for k,cap in bins.items()},20)};metrics={}
        for scope,(prediction,target,k) in vectors.items():metrics[scope]=compare(prediction,target,k);verify_metric(prediction,target,k,metrics[scope])
        comparisons={}
        for control in ['previous_native','raw_min_on','native_retained_on','all_NET_on','frozen216_primary']:
            reference=control216['metrics'] if control=='frozen216_primary' else prior['metrics']['cold'][control];checks=[]
            for scope in vectors:
                for metric in ['spearman','precision_at_k']:
                    a,b=metrics[scope][metric],reference[scope][metric];eps=1e-12 if metric=='spearman' else 0;checks.append(dict(scope=scope,metric=metric,candidate=a,reference=b,nonregression=a>=b-eps,strict=a>b+eps))
            comparisons[control]=dict(checks=checks,pass_comparison=all(x['nonregression'] for x in checks) and any(x['strict'] for x in checks))
        overflow=sum(max(0,val-caps[n]) for n,val in ledger.items());rows.append(dict(case=case,metrics=metrics,comparisons=comparisons,overflow_units=overflow,eligible_for_legal_route_commit=False));bindings.update({str(p):sha(p) for p in [lp,label,quality]});print('OWNER_CONTEXT_ORIGINAL_COLD_GATES',case,{k:x['pass_comparison'] for k,x in comparisons.items()},'overflow',overflow,flush=True)
    result=out/'results.json'
    with result.open('x') as f:json.dump(dict(status='ALL3_OWNER_CONTEXT_FULL_COLD_GATES_SCORED',rows=rows,bindings=bindings,scope='Old exposed development layouts only; no native utility, full-flow speed or hardware claim.'),f,indent=2,default=lambda v:str(v) if isinstance(v,Fraction) else None)
    helper=R/'tools/verify_MMC_complete_static_criticality_metrics_v2_2026_10_19.py'
    with (out/'independent_metric_verification_v1.json').open('x') as f:json.dump(dict(status='ALL6_OWNER_CONTEXT_METRIC_VECTORS_CROSSCHECKED',metric_vectors=6,bindings={str(p):sha(p) for p in [result,helper,Path(__file__).resolve()]}),f,indent=2)
if __name__=='__main__':main()
