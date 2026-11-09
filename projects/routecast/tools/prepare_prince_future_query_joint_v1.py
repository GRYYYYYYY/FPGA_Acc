"""Future native query distributions as labels; ready-only feature references."""
import json,struct
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'prince_future_query_joint_v1_2026-10-20';S=E/'prince_paired_cost_state_v1_2026-10-20';Q=E/'prince_connection_query_trial_v1_2026-10-20';P=E/'prince_cost_advance_ablation_trial_v1_2026-10-20';X=E/'prince_paired_exposure_features_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def number(w):return struct.unpack('<f',int(w).to_bytes(4,'little'))[0]
def main():
    D.mkdir(exist_ok=False)
    protocol=dict(status='FROZEN_BEFORE_FUTURE_QUERY_LABEL_EXTRACTION',scope='Original9cases,unchanged native policy,ready+1/+2 query targets only. No query afterready used as feature.',input='Reference already frozen ready occupancy/history,E,Q only;episode-grouping unchanged.',target='Perresource joint(A_bits,F_other,I_retained) histogram with original cost-call multiplicities and separate state-group counts. F_other=query_occ-I,not phase occupancy. A is global CHANNEL history before this search round.',denominator='Conditional on a linker-observed CHANNEL cost call. No-query resources have null moments and zero call count,not zero other-demand. No pooling two horizons as independent prefixes.',limits='Observed cost paths only,not all native path expansions. Factual native labels not intervention invariant. Perresource perphase A is fixed,so factual within-node covariance0;conditional feature-cell/case variation can still matter for predicting unknown A/F. No expected-cost/native admission.',bindings={str(p):sha(p) for p in [S/'frozen_inputs.json',X/'frozen_features.json',E/'prince_query_ledger_join_v1_2026-10-20/verification.json',Path(__file__)]})
    (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');proof=load(E/'prince_query_ledger_join_v1_2026-10-20/verification.json');bindings=dict(protocol['bindings']);rows=[];total_calls=total_groups=0;comparisons=0
    features={r['case']:r for r in load(X/'frozen_features.json')['rows']}
    for base in load(S/'frozen_inputs.json')['rows']:
        case=base['case']
        if base['status']=='NO_READY_EVENT':
            for h in [1,2]:rows.append(dict(case=case,horizon=h,status='NO_READY_EVENT'))
            continue
        t=base['ready_iteration'];src=Q/case/'capture';native=P/case/'native';states={}
        for i in [t,t+1,t+2]:
            for rel in [f'boundary/iteration_{i}.bin',f'owners/owners_{i}.bin']:
                a,b=src/rel,native/rel;assert a.read_bytes()==b.read_bytes();bindings[str(a)]=sha(a);bindings[str(b)]=sha(b);comparisons+=1
            raw=(src/'boundary'/f'iteration_{i}.bin').read_bytes();assert raw[:8]==b'RCBND001';states[i]={n:(kind,occ,cap,acc) for n,kind,occ,cap,acc in struct.iter_unpack('<QIiiI',raw[24:])}
        domain={r['id'] for r in map(json.loads,Path(base['feature_file']).open())};hist={1:defaultdict(Counter),2:defaultdict(Counter)};groups={1:Counter(),2:Counter()};qp=src/'queries.tsv';assert sha(qp)==proof['bindings'][str(qp)];bindings[str(qp)]=sha(qp)
        with qp.open() as f:
            for line in f:
                phase=int(line.split('\t',1)[0]);h=phase-t
                if h not in hist:continue
                i,encoded,node,kind,occ,cap,pres,acc,baseword,cost,nc,active,ident,pin,sink,owned,count=map(int,line.split())
                if kind not in [4,5]:continue
                assert node in domain and cap==1 and owned in [0,1] and occ>=owned and count>0 and active==1 and nc==0
                assert acc==states[phase-1][node][3];a=number(acc);assert a==int(a) and a>=1
                hist[h][node][acc,occ-owned,owned]+=count;groups[h][node]+=1
        for h in [1,2]:
            folder=D/case;folder.mkdir(parents=True,exist_ok=True);out=folder/f'query_joint_h{h}.jsonl';calls=ng=queried=0
            with out.open('x') as f:
                for node in sorted(domain):
                    c=hist[h][node];n=sum(c.values());calls+=n;ng+=groups[h][node];queried+=bool(n)
                    sums=dict(A=0,F_other=0,A_F_other=0,I_retained=0,A_I_retained=0)
                    for (acc,other,own),count in c.items():
                        a=int(number(acc));sums['A']+=a*count;sums['F_other']+=other*count;sums['A_F_other']+=a*other*count;sums['I_retained']+=own*count;sums['A_I_retained']+=a*own*count
                    if n:assert n*sums['A_F_other']==sums['A']*sums['F_other']
                    f.write(json.dumps(dict(id=node,calls=n,state_groups=groups[h][node],moment_sums=sums if n else None,joint=[dict(acc_bits=a,F_other=o,I_retained=i,calls=v) for (a,o,i),v in sorted(c.items())]),separators=(',',':'))+'\n')
            rows.append(dict(case=case,horizon=h,status='FUTURE_QUERY_LABELS_EXTRACTED',ready_iteration=t,query_iteration=t+h,resources=len(domain),queried_resources=queried,no_query_resources=len(domain)-queried,cost_calls=calls,state_groups=ng,target_file=str(out),ready_feature_file=features[case]['features']));bindings[str(out)]=sha(out);bindings[features[case]['features']]=sha(features[case]['features']);total_calls+=calls;total_groups+=ng
            print('QUERY_JOINT_LABELS',case,h,calls,queried,flush=True)
    with (D/'dataset_manifest.json').open('x') as f:json.dump(dict(status='FUTURE_QUERY_JOINT_LABELS_EXTRACTED_PENDING_AUDIT',rows=rows,cost_calls=total_calls,state_groups=total_groups,snapshot_byte_comparisons=comparisons,original_full9_gate=False,bindings=bindings),f,indent=2);f.write('\n')
if __name__=='__main__':main()
