"""Evaluate target-using aggregate oracle on unchanged full cold quality domains."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
from prediction_metrics import compare
from verify_MMC_complete_static_criticality_metrics_v2_2026_10_19 import verify_metric

R=Path(__file__).resolve().parents[1]


def main():
    pp=R/'experiments/mmc_aggregate_L1_oracle_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());assert all(sha(p)==h for p,h in plan['bindings'].items())
    source=R/'experiments/mmc_aggregate_L1_oracle_v1_2026-10-19';rp=source/'receipt.json';review=json.loads(rp.read_text());proof=source/'independent_verification_v1.json';verified=json.loads(proof.read_text());assert verified['status']=='ALL3_AGGREGATE_ORACLE_WEIGHTS_BANK_BINDINGS_FLOWCUT_AND_DIRECT_LOSSES_VERIFIED' and verified['bindings'][str(rp)]==sha(rp)
    out=R/'experiments/mmc_aggregate_L1_oracle_quality_v1_2026-10-19';out.mkdir(exist_ok=False)
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
    bindings={str(p):sha(p) for p in [pp,rp,proof,original,graph,Path(__file__).resolve()]};rows=[]
    for item in inputs['cases']:
        case=item['case'];row=next(x for x in review['rows'] if x['case']==case);chosen={x['net_id'] for x in map(json.loads,(source/case/'choices.jsonl').open()) if x['pick']=='B'};bank=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/case/'banks.jsonl';assert review['bindings'][str(bank)]==sha(bank);ledger=Counter();nets=set()
        for x in map(json.loads,bank.open()):assert x['net_id'] not in nets;nets.add(x['net_id']);ledger.update(x['B'] if x['net_id'] in chosen else x['A'])
        assert len(nets)==55300
        overflow=sum(max(0,v-caps[n]) for n,v in ledger.items());assert overflow==row['overflow_units']
        label=Path(item['native_label']);truth={int(n):v for n,v in json.loads(label.read_text())['node_occupancy'].items()};quality=Path(item['quality_reference_protocol']).with_name('comparison.json');prior=json.loads(quality.read_text());vp=quality.with_name('verification.json');v=json.loads(vp.read_text());assert v['status']=='pass' and v['bindings'][str(quality)]==sha(quality)
        sp,st=Counter(),Counter()
        for n,keys in channels.items():
            for k in keys:sp[k]+=ledger[n];st[k]+=truth.get(n,0)
        vectors={'concrete':({n:Fraction(ledger[n],caps[n]) for n in channels},{n:Fraction(truth.get(n,0),caps[n]) for n in channels},12936),'spatial':({k:Fraction(sp[k],cap) for k,cap in bins.items()},{k:Fraction(st[k],cap) for k,cap in bins.items()},20)}
        metrics={}
        for scope,(prediction,target,k) in vectors.items():metrics[scope]=compare(prediction,target,k);verify_metric(prediction,target,k,metrics[scope])
        comparisons={}
        for control in ['previous_native','raw_min_on','native_retained_on','all_NET_on']:
            checks=[]
            for scope in vectors:
                for metric in ['spearman','precision_at_k']:
                    a=metrics[scope][metric];b=prior['metrics']['cold'][control][scope][metric];eps=1e-12 if metric=='spearman' else 0;checks.append(dict(scope=scope,metric=metric,candidate=a,reference=b,nonregression=a>=b-eps,strict=a>b+eps))
            comparisons[control]=dict(checks=checks,pass_comparison=all(x['nonregression'] for x in checks) and any(x['strict'] for x in checks))
        path=out/(case+'.ledger.json')
        with path.open('x') as f:json.dump(dict(ledger),f)
        rows.append(dict(case=case,selected_B_NETs=len(chosen),metrics=metrics,comparisons=comparisons,overflow_units=overflow,eligible_for_legal_route_commit=False))
        bindings.update({str(p):sha(p) for p in [bank,label,quality,vp,path]});print('AGGREGATE_ORACLE_COLD_QUALITY',case,{k:v['pass_comparison'] for k,v in comparisons.items()},'overflow',overflow,flush=True)
    result=out/'results.json'
    with result.open('x') as f:json.dump(dict(status='ALL3_TARGET_USING_AGGREGATE_ORACLE_COLD_QUALITY_SCORED',rows=rows,bindings=bindings,scope=plan['scope']),f,indent=2,default=lambda v:str(v) if isinstance(v,Fraction) else None)
    helper=R/'tools/verify_MMC_complete_static_criticality_metrics_v2_2026_10_19.py'
    with (out/'independent_metric_verification_v1.json').open('x') as f:json.dump(dict(status='ALL6_CLOSED_CHOICE_METRICS_HISTOGRAM_TOPK_MAE_CROSSCHECK_PASS',metric_vectors=6,bindings={str(p):sha(p) for p in [result,helper,Path(__file__).resolve()]},scope='Independent numerical routine in evaluation process; graph, physical bank membership and closures independently verified separately. Metric checks only; full original all3 comparisons and complete costs remain required.'),f,indent=2)


if __name__=='__main__':main()
