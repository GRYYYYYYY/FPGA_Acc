"""Retrospective matched-target and fixed-TopK displacement diagnosis."""
import json
from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction as F
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'prince_tail_final_gate_v1_2026-10-20'
S=E/'prince_paired_cost_state_v1_2026-10-20'
X=E/'prince_paired_exposure_features_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
    verified=load(D/'verification.json')
    audit=load(D/'independent_verification_v1.json')
    for p,h in audit['bindings'].items():assert sha(p)==h
    features={r['case']:r for r in load(X/'frozen_features.json')['rows']}
    targets={(r['case'],r['mode'],r['horizon']):r for r in load(S/'dataset_manifest.json')['rows']}
    summaries=[];cells=[];bindings={str(p):sha(p) for p in [D/'verification.json',D/'independent_verification_v1.json',Path(__file__)]}
    for case in verified['rows']:
        c=case['case']
        if case['status']=='NO_READY_EVENT':summaries.append(dict(case=c,status='NO_READY_EVENT'));continue
        fp=Path(features[c]['features']);ready={r['id']:r for r in map(json.loads,fp.open())}
        tp=Path(targets[c,'native',1]['target_file']);phase={r['id']:r['positive_occupancy'] for r in map(json.loads,tp.open())}
        sp=E/'prince_feedback_quality_v1_2026-10-20'/c/'specification.json';lp=Path(load(sp)['label_physical_audit']);final={int(n):v for n,v in load(lp)['node_occupancy'].items()};assert set(phase)==set(ready)
        transition=Counter();grouped=defaultdict(Counter)
        for node,r in ready.items():
            a=int(r['occupancy']>0);b=phase[node];z=final.get(node,0);assert z in [0,1];transition[a,b,z]+=1;grouped[r['occupancy'],r['acc_bits'],r['Q']][b,z]+=1
        for key,counts in sorted(grouped.items()):
            n=sum(counts.values());p=sum(v for (b,z),v in counts.items() if b);z=sum(v for (b,z),v in counts.items() if z)
            cells.append(dict(case=c,key=list(key),resources=n,phase_positive=p,final_positive=z,final_minus_phase_rate=[z-p,n],joint=[dict(phase=b,final=z,resources=v) for (b,z),v in sorted(counts.items())]))
        metrics=case['horizons']['1']['metrics']['resource'];selected=set(metrics['prediction_top_k']);target=set(metrics['truth_top_k']);assert selected<=set(ready) and target<=set(ready)
        # Original cap1 final labels tie at 1; verify the actual fixed target rule explicitly.
        positives=sorted(n for n in ready if final.get(n,0)>0);assert target==set(positives[:len(target)])
        actual=sum(final.get(n,0)>0 for n in selected);fixed=len(selected&target)
        cp=sp.parent/'comparison.json';original=load(cp)['metrics']['previous_native']['resource'];baseline=set(original['prediction_top_k'])
        summary=dict(case=c,status='DIAGNOSED',resources=len(ready),
                     transitions=[dict(ready=a,phase=b,final=z,resources=v) for (a,b,z),v in sorted(transition.items())],
                     phase_final_disagreements=sum(v for (a,b,z),v in transition.items() if b!=z),
                     primary_topK=len(selected),fixed_target_hits=fixed,selected_final_occupied=actual,
                     selected_final_empty=len(selected)-actual,selected_final_occupied_outside_fixed_target=actual-fixed,
                     previous_fixed_target_hits=len(baseline&target),previous_selected_final_occupied=sum(final.get(n,0)>0 for n in baseline),
                     interpretation='Final-occupied purity and fixed-target TopK intersection are distinct diagnostics;neither replaces original gate.')
        assert fixed==metrics['top_k_hits'];summaries.append(summary)
        for p in [fp,tp,sp,lp,cp]:bindings[str(p)]=sha(p)
        print(c,'phase/final different',summary['phase_final_disagreements'],'TopK',fixed,'actual occupied',actual,'/',len(selected),flush=True)
    out=dict(status='MATCHED_PHASE_FINAL_TRANSITIONS_AND_TOPK_DISPLACEMENT_DIAGNOSED',rows=summaries,cells=cells,original_full9_gate=False,
             scope='Retrospective diagnosis;final labels used only here. Exact stock cells are descriptive populations,not learned IDs or deployed oracle ordering. Original gate unchanged.',bindings=bindings)
    with (D/'phase_final_displacement_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
if __name__=='__main__':main()
