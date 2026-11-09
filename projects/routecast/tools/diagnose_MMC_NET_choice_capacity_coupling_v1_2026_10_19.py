"""Separate newly introduced cross-candidate capacity conflicts from inherited ones."""
import json,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter,defaultdict
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    source=R/'experiments/mmc_complete_NET_choice_diagnostic_v1_2026-10-19';rp=source/'results.json';d=json.loads(rp.read_text());proof=source/'independent_verification_v1.json';v=json.loads(proof.read_text());assert v['status']=='ALL3_COMPLETE_NET_CHOICES_LEDGER_OVERFLOW_SIX_METRICS_AND_COMPARISONS_VERIFIED' and v['bindings'][str(rp)]==sha(rp)
    pp=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());out=R/'experiments/mmc_NET_choice_capacity_coupling_v1_2026-10-19';out.mkdir(exist_ok=False)
    graph=Path(json.loads(Path(plan['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);caps=array('I');stack=[]
    class NodesDone(Exception):pass
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':assert int(a['id'])==len(caps);caps.append(int(a['capacity']))
        stack.append(tag)
    def closing(tag):
        assert stack.pop()==tag
        if tag=='rr_nodes':raise NodesDone()
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    try:
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    except NodesDone:pass
    assert len(caps)==904438
    bindings={str(p):sha(p) for p in [rp,proof,pp,graph,Path(__file__).resolve()]};rows=[]
    for item in plan['cases']:
        case=item['case'];cp=source/case/'choices.jsonl';lp=source/case/'ledger.json';assert d['bindings'][str(cp)]==sha(cp) and d['bindings'][str(lp)]==sha(lp)
        mix={int(n):c for n,c in json.loads(lp.read_text()).items()};full=[]
        for key in ['candidate_A','candidate_B']:
            path=Path(item[key]);assert plan['bindings'][str(path)]==sha(path);full.append({int(n):c for n,c in json.loads(path.read_text())['ledger'].items()});bindings[str(path)]=sha(path)
        bad={n for n,c in mix.items() if c>caps[n]};owners={n:{'A':set(),'B':set()} for n in bad};contributions={'A':Counter(),'B':Counter()}
        for line in cp.open():
            x=json.loads(line)
            for n in x['owned']:
                contributions[x['pick']][n]+=1
                if n in bad:owners[n][x['pick']].add(x['net_id'])
        assert contributions['A']+contributions['B']==Counter(mix)
        counts=Counter();edges=set();target=out/(case+'.conflicts.jsonl')
        with target.open('x') as f:
            for n in sorted(bad):
                a,b=full[0].get(n,0),full[1].get(n,0);new=a<=caps[n] and b<=caps[n];units=mix[n]-caps[n]
                group='new_between_individually_nonoverused_banks' if new else 'at_least_one_bank_already_overused'
                counts[group+'_resources']+=1;counts[group+'_units']+=units
                if new:assert owners[n]['A'] and owners[n]['B']
                assert len(owners[n]['A'])+len(owners[n]['B'])==mix[n]
                for bn in owners[n]['B']:
                    for an in owners[n]['A']:edges.add((bn,an))
                f.write(json.dumps(dict(node=n,capacity=caps[n],full_A=a,full_B=b,mixed=mix[n],new_conflict=new,A_selected_NETs=sorted(owners[n]['A']),B_selected_NETs=sorted(owners[n]['B'])),separators=(',',':'))+'\n')
        assert sum(v for k,v in counts.items() if k.endswith('_units'))==next(x for x in d['cases'] if x['case']==case)['overflow_units']
        rows.append(dict(case=case,counts=dict(counts),cross_bank_B_to_A_owner_pairs=len(edges)))
        bindings.update({str(p):sha(p) for p in [cp,lp,target]});print('CAPACITY_COUPLING',case,dict(counts),flush=True)
    (out/'diagnosis.json').write_text(json.dumps(dict(status='ALL3_CHOICE_NEW_CROSS_BANK_CAPACITY_CONFLICTS_ACCOUNTED',rows=rows,bindings=bindings,
        scope='Exact capacity accounting on independently verified label-guided choices. Candidate owner sets are physically valid individually; combination need not be globally capacity-compatible. Dependencies are descriptive, not a new chooser or causal rank-metric attribution.'),indent=2)+'\n')


if __name__=='__main__':main()
