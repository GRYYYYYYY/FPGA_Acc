"""Original bank membership, complete edge witnesses, SCC certificates and repairs."""
import json,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter,defaultdict,deque
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';rp=root/'review.json';d=json.loads(rp.read_text());assert all(sha(p)==h for p,h in d['bindings'].items())
    pp=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());graph=Path(json.loads(Path(plan['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);caps=array('I');dest=array('I');stack=[]
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':caps.append(int(a['capacity']))
        elif tag=='edge' and stack and stack[-1]=='rr_edges':dest.append(int(a['sink_node']))
        stack.append(tag)
    def closing(tag):assert stack.pop()==tag
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    with graph.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    parser.Parse(b'',True);assert len(caps)==904438 and len(dest)==8097539;rows=[]
    for item in plan['cases']:
        case=item['case'];row=next(x for x in d['rows'] if x['case']==case);g=json.loads((root/case/'graph.json').read_text());banks=[{},{}]
        for x in map(json.loads,(root/case/'banks.jsonl').open()):
            net=x['net_id'];assert net not in banks[0]
            for i,key in enumerate(['A','B']):assert len(x[key])==len(set(x[key]));banks[i][net]=set(x[key])
        owners=[];full_ledgers=[]
        for i,key in enumerate(['candidate_A','candidate_B']):
            actual=defaultdict(set);frame=json.loads(Path(item[key]).read_text())
            for x in frame['records']:
                actual[x['net_id']].add(x['source'])
                for edge in x['answer']['physical_edge_ids']:actual[x['net_id']].add(dest[edge])
            assert actual==banks[i]
            inverted=defaultdict(set)
            for net,nodes in actual.items():
                for node in nodes:inverted[node].add(net)
            owners.append(inverted);ledger=Counter({n:len(nets) for n,nets in inverted.items()});assert dict(ledger)=={int(n):v for n,v in frame['ledger'].items()};full_ledgers.append(ledger)
        eligible=set();expected=defaultdict(set)
        for n in owners[0].keys()|owners[1].keys():
            a,b=owners[0].get(n,set()),owners[1].get(n,set())
            if caps[n]==1 and len(a)==len(b)==1:
                eligible.add(n);u=next(iter(b));v=next(iter(a))
                if u!=v:expected[u,v].add(n)
        assert set(g['eligible_resources'])==eligible and len(g['eligible_resources'])==len(eligible)
        actual_edges={(x['source'],x['target']):set(x['resources']) for x in g['edges']};assert actual_edges==expected and len(actual_edges)==len(g['edges'])
        nodes=set(g['nodes']);assert nodes==set(banks[0])==set(banks[1]) and len(nodes)==55300
        forward=defaultdict(set);reverse=defaultdict(set)
        for u,v in actual_edges:forward[u].add(v);reverse[v].add(u)
        groups=[set(x) for x in g['components']];ids={};seen=set()
        for i,group in enumerate(groups):
            assert group and not seen&group;seen.update(group)
            for net in group:ids[net]=i
            for adjacency in [forward,reverse]:
                reached={min(group)};pending=list(reached)
                while pending:
                    for v in adjacency[pending.pop()]&group:
                        if v not in reached:reached.add(v);pending.append(v)
                assert reached==group
        assert seen==nodes
        dag={(ids[u],ids[v]) for u,v in actual_edges if ids[u]!=ids[v]};assert dag==set(map(tuple,g['condensation_edges']))
        indegree=Counter(v for u,v in dag);outgoing=defaultdict(list)
        for u,v in dag:outgoing[u].append(v)
        pending=deque(i for i in range(len(groups)) if indegree[i]==0);removed=0
        while pending:
            u=pending.popleft();removed+=1
            for v in outgoing[u]:
                indegree[v]-=1
                if indegree[v]==0:pending.append(v)
        assert removed==len(groups)
        teacher={x['net_id'] for x in map(json.loads,(R/'experiments/mmc_complete_NET_choice_diagnostic_v1_2026-10-19'/case/'choices.jsonl').open()) if x['pick']=='B'}
        seeds={'all_A':set(),'all_B':nodes,'NETid_mod7':{n for n in nodes if n%7==0},'archived_label_guided_diagnostic':teacher}
        for check in row['closure_checks']:
            seed=seeds[check['seed']];fixed=set(seed)
            while True:
                nxt=fixed|{v for u,v in actual_edges if u in fixed}
                if nxt==fixed:break
                fixed=nxt
            assert fixed==set(check['closed_B_NET_ids']) and len(fixed)==check['closed_B_NETs'] and len(seed)==check['seed_B_NETs']
            violations={(u,v) for u,v in actual_edges if u in seed and v not in seed};assert len(violations)==check['violated_edges_before']
            for selected,when in [(seed,'before'),(fixed,'after')]:
                ledger=full_ledgers[0].copy()
                for net in selected:ledger.subtract(banks[0][net]);ledger.update(banks[1][net])
                bad={n for n in eligible if ledger[n]>1};assert len(bad)==check['protected_overused_resources_'+when]
                if when=='before':assert bad=={n for edge in violations for n in actual_edges[edge]}
                else:assert not bad
                assert sum(max(0,v-caps[n]) for n,v in ledger.items())==check['full_overflow_'+when]
        rows.append(dict(case=case,NETs=len(nodes),resource_witnesses=sum(map(len,expected.values())),closure_patterns=len(row['closure_checks'])));print('OWNERSHIP_IMPLICATION_WITNESSES_SCC_CERTIFICATES_AND_CLOSURES_PASS',case,flush=True)
    assert len(rows)==3
    with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_ORIGINAL_BANKS_COMPLETE_IMPLICATIONS_SCC_AND_TWELVE_CLOSURES_VERIFIED',rows=rows,bindings={str(p):sha(p) for p in [rp,Path(__file__).resolve()]},scope='Capacity1 and unique-owner-per-bank domain. Independent SCC certificate and fixed-point repair verification; physical path admission inherited. No prediction quality or global legalization claim.'),f,indent=2)


if __name__=='__main__':main()
