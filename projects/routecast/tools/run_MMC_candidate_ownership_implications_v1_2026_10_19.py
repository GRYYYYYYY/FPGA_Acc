"""Input-only complete-tree ownership graph; archived oracle seed is diagnostic only."""
import json,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from NET_candidate_ownership_implications_v1 import build,close,components
from pre_route_endpoints import sha
from versioned_digest_cache_v1 import Cache

R=Path(__file__).resolve().parents[1]


def main():
    pp=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());out=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';out.mkdir(exist_ok=False)
    contract=R/'experiments/NET_candidate_ownership_implications_contract_v1_2026-10-19/verification.json';proof=json.loads(contract.read_text());assert proof['status']=='EXHAUSTIVE_OWNER_CAPACITY_THEOREM_MINIMAL_CLOSURE_AND_SCC_PASS'
    bindings={str(p):sha(p) for p in [pp,contract,Path(__file__).resolve(),R/'tools/NET_candidate_ownership_implications_v1.py']};cache=Cache()
    with cache.installed():
        assert all(sha(p)==h for p,h in proof['bindings'].items());assert all(sha(p)==h for p,h in plan['bindings'].items())
        graph=Path(json.loads(Path(plan['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);caps=array('I');dest=array('I');stack=[]
        def opening(tag,a):
            if tag=='node' and stack and stack[-1]=='rr_nodes':assert int(a['id'])==len(caps);caps.append(int(a['capacity']))
            elif tag=='edge' and stack and stack[-1]=='rr_edges':dest.append(int(a['sink_node']))
            stack.append(tag)
        def closing(tag):assert stack.pop()==tag
        parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
        parser.Parse(b'',True);assert len(caps)==904438 and len(dest)==8097539;bindings[str(graph)]=sha(graph);rows=[]
        for item in plan['cases']:
            case=item['case'];directory=out/case;directory.mkdir();banks=[];owners=[]
            for key in ['candidate_A','candidate_B']:
                p=Path(item[key]);frame=json.loads(p.read_text());bank=defaultdict(set)
                for r in frame['records']:bank[r['net_id']].add(r['source']);bank[r['net_id']].update(dest[e] for e in r['answer']['physical_edge_ids'])
                inverted=defaultdict(set)
                for net,nodes in bank.items():
                    for node in nodes:inverted[node].add(net)
                assert {n:len(nets) for n,nets in inverted.items()}=={int(n):v for n,v in frame['ledger'].items()}
                banks.append(bank);owners.append(inverted);bindings[str(p)]=sha(p)
            assert set(banks[0])==set(banks[1]) and len(banks[0])==55300
            g=build(banks[0],owners[0],owners[1],caps);scc=components(g);eligible=set(g['eligible_resources']);component={net:i for i,group in enumerate(scc) for net in group};dag={(component[u],component[v]) for u,v in g['edges'] if component[u]!=component[v]}
            gp=directory/'graph.json';gp.write_text(json.dumps(dict(nodes=g['nodes'],eligible_resources=g['eligible_resources'],edges=[dict(source=u,target=v,resources=g['witnesses'][u,v]) for u,v in g['edges']],components=scc,condensation_edges=sorted(dag)),separators=(',',':'))+'\n')
            bp=directory/'banks.jsonl'
            with bp.open('x') as f:
                for net in g['nodes']:f.write(json.dumps(dict(net_id=net,A=sorted(banks[0][net]),B=sorted(banks[1][net])),separators=(',',':'))+'\n')
            choices=R/'experiments/mmc_complete_NET_choice_diagnostic_v1_2026-10-19'/case/'choices.jsonl';teacher={x['net_id'] for x in map(json.loads,choices.open()) if x['pick']=='B'}
            seeds={'all_A':set(),'all_B':set(g['nodes']),'NETid_mod7':{n for n in g['nodes'] if n%7==0},'archived_label_guided_diagnostic':teacher};checks=[]
            for name,seed in seeds.items():
                closed=close(g,seed);assert seed<=closed and all(u not in closed or v in closed for u,v in g['edges']);violated=[(u,v) for u,v in g['edges'] if u in seed and v not in seed];witnesses={n for edge in violated for n in g['witnesses'][edge]}
                ledgers=[]
                for chosen in [seed,closed]:
                    ledger=Counter(n for net in g['nodes'] for n in banks[net in chosen][net]);ledgers.append(ledger)
                initial_bad={n for n in eligible if ledgers[0][n]>1};final_bad={n for n in eligible if ledgers[1][n]>1};assert initial_bad==witnesses and not final_bad
                checks.append(dict(seed=name,seed_B_NETs=len(seed),closed_B_NETs=len(closed),violated_edges_before=len(violated),protected_overused_resources_before=len(initial_bad),protected_overused_resources_after=0,full_overflow_before=sum(max(0,v-caps[n]) for n,v in ledgers[0].items()),full_overflow_after=sum(max(0,v-caps[n]) for n,v in ledgers[1].items()),closed_B_NET_ids=sorted(closed)))
            row=dict(case=case,NETs=len(g['nodes']),eligible_resources=len(eligible),implication_edges=len(g['edges']),resource_witnesses=sum(len(x) for x in g['witnesses'].values()),SCCs=len(scc),nontrivial_SCCs=sum(len(x)>1 for x in scc),largest_SCC=max(map(len,scc)),condensation_edges=len(dag),closure_checks=checks);rows.append(row)
            bindings.update({str(p):sha(p) for p in [gp,bp,choices]});print('OWNERSHIP_GRAPH_COMPLETE',case,'edges',len(g['edges']),'largest_SCC',row['largest_SCC'],'teacher_repair',[(x['seed_B_NETs'],x['closed_B_NETs'],x['full_overflow_before'],x['full_overflow_after']) for x in checks if x['seed']=='archived_label_guided_diagnostic'],flush=True)
        (out/'review.json').write_text(json.dumps(dict(status='ALL3_INPUT_ONLY_OWNERSHIP_GRAPHS_AND_PROTECTED_DOMAIN_CLOSURES_PRODUCED',rows=rows,bindings=bindings,scope='Graph uses complete candidate bank ownership and capacities only. Archived label-guided seed is retrospective repair diagnostic; other seeds are fixed input-only tests. No global legalization, quality or deployable chooser claim; excluded capacities/overused-bank resources remain explicit.',independent_verification_pending=True),indent=2)+'\n')


if __name__=='__main__':main()
