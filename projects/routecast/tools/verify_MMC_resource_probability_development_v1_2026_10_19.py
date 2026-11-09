"""Independent train histograms, rational probabilities, resource scatter and cuts."""
import json,xml.parsers.expat as expat
from pathlib import Path
from array import array
from fractions import Fraction
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from maximum_weight_NET_closure_v1 import verify

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_resource_probability_development_v1_2026-10-19';rp=root/'receipt.json';d=json.loads(rp.read_text());assert d['status']=='ALL6_FIXED_RESOURCE_FREQUENCY_FOLDS_AND_CLOSED_CHOICES_PRODUCED' and all(sha(p)==h for p,h in d['bindings'].items())
    pp=R/'experiments/mmc_resource_probability_development_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());context=R/'experiments/mmc_resource_context_v1_2026-10-19';nodes=array('I');nodes.frombytes((context/'CHANNEL_ids.u32').read_bytes());channel=set(nodes);source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';original=json.loads((R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json').read_text());items={x['case']:x for x in original['cases']};caps=array('I');stack=[]
    class Done(Exception):pass
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':caps.append(int(a['capacity']))
        stack.append(tag)
    def closing(tag):
        assert stack.pop()==tag
        if tag=='rr_nodes':raise Done()
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    with (R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml').open('rb') as f:
        try:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
        except Done:pass
    def codes(case):
        a=array('H');a.frombytes((context/(case+'.u16')).read_bytes());assert len(a)==258720;return a
    def projected(code,with_prefix):
        if with_prefix:return code
        q=code//4;return ((q//27*3+(q%27)//9)*3+(q%9)//3)*4+code%4
    rows=[]
    for fold in plan['folds']:
        case=fold['evaluation_case'];train=fold['training_cases'];g=json.loads((source/case/'graph.json').read_text());banks={x['net_id']:x for x in map(json.loads,(source/case/'banks.jsonl').open())};owners=[defaultdict(set),defaultdict(set)];A=Counter()
        for net,x in banks.items():
            A.update(x['A'])
            for i,key in enumerate(['A','B']):
                for n in x[key]:
                    if n in channel:owners[i][n].add(net)
        safe={n for n in channel if len(owners[0][n])<=1 and len(owners[1][n])<=1};test=codes(case)
        for arm in [plan['primary_arm'],plan['ablation_arm']]:
            row=next(x for x in d['rows'] if (x['case'],x['arm'])==(case,arm));directory=root/case/arm;m=json.loads((directory/'model.json').read_text());assert m['training_cases']==sorted(train) and m['evaluation_case']==case and case not in train;assert m['with_prefix']==(arm==plan['primary_arm'])
            expected_paths={str(p) for c in train for p in [context/(c+'.u16'),Path(items[c]['native_label'])]};assert set(m['training_bindings'])==expected_paths and all(sha(p)==h for p,h in m['training_bindings'].items());joint=Counter()
            for c in train:
                target={int(n):v for n,v in json.loads(Path(items[c]['native_label']).read_text())['node_occupancy'].items()}
                for code,n in zip(codes(c),nodes):joint[projected(code,m['with_prefix']),target.get(n,0)]+=1
            size=216 if m['with_prefix'] else 72;N=[joint[i,0]+joint[i,1] for i in range(size)];S=[joint[i,1] for i in range(size)];assert N==m['counts'] and S==m['occupied'] and sum(N)==m['training_resources']==517440
            table=[round(Fraction(10**6*(s+1),n+2)) for s,n in zip(S,N)];assert table==m['probability_int'];prob=array('I');prob.frombytes((directory/'probabilities.u32').read_bytes());assert len(prob)==258720 and list(prob)==[table[projected(c,m['with_prefix'])] for c in test]
            expected={n:0 for n in banks}
            for n,p in zip(nodes,prob):
                if n not in safe:continue
                coefficient=10**6-2*p
                for net in owners[0][n]:expected[net]+=coefficient
                for net in owners[1][n]:expected[net]-=coefficient
            choice={x['net_id']:x for x in map(json.loads,(directory/'choices.jsonl').open())};assert set(choice)==set(banks);selected=set();encoded={}
            for net,w in expected.items():
                x=choice[net];assert x['expected_gain_scaled']==w and x['encoded_weight']==55301*w-1 and x['pick'] in ['A','B'];encoded[net]=x['encoded_weight']
                if x['pick']=='B':selected.add(net)
            groups=g['components'];cw={i:sum(encoded[n] for n in c) for i,c in enumerate(groups)};certificate=json.loads((directory/'flow_cut_certificate.json').read_text());objective=verify(cw,list(map(tuple,g['condensation_edges'])),certificate);assert {n for i in certificate['selected'] for n in groups[i]}==selected and all(e['source'] not in selected or e['target'] in selected for e in g['edges']);gain=sum(expected[n] for n in selected);assert objective==55301*gain-len(selected) and gain==row['expected_safe_L1_gain_scaled']
            ledger=A.copy()
            for net in selected:ledger.subtract(banks[net]['A']);ledger.update(banks[net]['B'])
            assert {n:v for n,v in ledger.items() if v}=={int(n):v for n,v in json.loads((directory/'ledger.json').read_text()).items()};assert all(ledger[n]<=1 for n in safe) and all(ledger[n]<=1 for n in g['eligible_resources']);assert len(selected)==row['B_NETs'];changed=sum(banks[n]['A']!=banks[n]['B'] for n in selected);assert changed==row['actual_NET_ownership_changes']
            rows.append(dict(case=case,arm=arm,training_resources=517440,actual_NET_ownership_changes=changed,full_overflow_units=sum(max(0,v-caps[n]) for n,v in ledger.items())));print('RESOURCE_FREQUENCY_HISTOGRAMS_PROBABILITIES_FLOWCUT_LEDGER_PASS',case,arm,'overflow',rows[-1]['full_overflow_units'],flush=True)
    assert len(rows)==6
    with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL6_TRAIN_ONLY_RESOURCE_COUNTS_EXACT_PROBABILITIES_CLOSED_CHOICES_AND_LEDGER_VERIFIED',rows=rows,bindings={str(p):sha(p) for p in [rp,pp,Path(__file__).resolve()]},scope='Independent joint histograms/rational rounding/resource-scatter weights and exact primal flow/cut. Eval target labels excluded from model counts; all old layouts exposed. No full capacity or forecast quality claim.'),f,indent=2)


if __name__=='__main__':main()
