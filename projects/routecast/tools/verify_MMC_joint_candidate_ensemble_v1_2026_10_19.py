"""Original-bank coverage and independent60digit closed-state recurrence checks."""
import json,math,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter,defaultdict
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
SCALE=10**12


def main():
    root=R/'experiments/mmc_joint_candidate_ensemble_v1_2026-10-19';rp=root/'receipt.json';d=json.loads(rp.read_text());assert d['status']=='ALL3_FROZEN_COMPLETE_BANK_JOINT_ENSEMBLES_PRODUCED' and d['target_labels_read'] is False and all(sha(p)==h for p,h in d['bindings'].items())
    pp=R/'experiments/mmc_joint_candidate_ensemble_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';context=R/'experiments/mmc_resource_context_v1_2026-10-19';nodes=array('I');nodes.frombytes((context/'CHANNEL_ids.u32').read_bytes());channel=set(nodes);original=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';lineage=json.loads(original.read_text());items={x['case']:x for x in lineage['cases']};graph=next(Path(p) for p in d['bindings'] if p.endswith('rr_graph.xml'));caps=array('I');dest=array('I');stack=[]
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':caps.append(int(a['capacity']))
        elif tag=='edge' and stack and stack[-1]=='rr_edges':dest.append(int(a['sink_node']))
        stack.append(tag)
    def closing(tag):assert stack.pop()==tag
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    with graph.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    parser.Parse(b'',True);assert len(caps)==904438 and len(dest)==8097539;rows=[];bindings={str(p):sha(p) for p in [rp,pp,Path(__file__).resolve()]}
    with localcontext() as arithmetic:
        arithmetic.prec=60;arithmetic.Emax=10**9;arithmetic.Emin=-10**9;ln2=Decimal(2).ln()
        for row in d['rows']:
            case=row['case'];directory=root/case;g=json.loads((source/case/'graph.json').read_text());groups=g['components'];component={net:i for i,c in enumerate(groups) for net in c};banks={x['net_id']:x for x in map(json.loads,(source/case/'banks.jsonl').open())};ep=Path(items[case]['endpoint']);queries={q['connection_id']:q for q in json.loads(ep.read_text())['connections']};assert len(queries)==115572
            for key,bankkey in [('candidate_A','A'),('candidate_B','B')]:
                path=Path(items[case][key]);assert lineage['bindings'][str(path)]==sha(path);frame=json.loads(path.read_text());records={x['connection_id']:x for x in frame['records']};assert len(records)==len(frame['records'])==115572 and set(records)==set(queries);owned=defaultdict(set)
                for cid,x in records.items():
                    q=queries[cid];assert all(x[k]==v for k,v in q.items()) and x['answer']['delay']<=x['budget_integer'];owned[q['net_id']].add(q['source']);owned[q['net_id']].update(dest[e] for e in x['answer']['physical_edge_ids'])
                assert set(owned)==set(banks) and all(owned[n]==set(banks[n][bankkey]) for n in banks)
            A=defaultdict(set);B=defaultdict(set)
            for net,b in banks.items():
                for n in b['A']:A[n].add(net)
                for n in b['B']:B[n].add(net)
            safe={n for n in channel if len(A[n])<=1 and len(B[n])<=1};codes=array('H');codes.frombytes((context/(case+'.u16')).read_bytes());category=dict(zip(nodes,codes));mp=R/'experiments/mmc_resource_probability_development_v1_2026-10-19'/case/'history_A_B_prefix_direction_segment/model.json';assert plan['bindings'][str(mp)]==sha(mp);model=json.loads(mp.read_text());assert case not in model['training_cases'];odds=[Decimal(s+1).ln()-Decimal(n-s+1).ln() for n,s in zip(model['counts'],model['occupied'])];delta=defaultdict(Counter)
            for net,b in banks.items():
                for n in (set(b['B'])-set(b['A']))&safe:delta[component[net]][category[n]]+=1
                for n in (set(b['A'])-set(b['B']))&safe:delta[component[net]][category[n]]-=1
            theta=[sum((Decimal(v)*odds[k] for k,v in delta[i].items() if v),Decimal()) for i in range(len(groups))];reported_logits=json.loads((directory/'component_logits.json').read_text());raw_marginals=json.loads((directory/'component_marginals.json').read_text());assert all(math.isclose(float(a),b,rel_tol=1e-12,abs_tol=1e-9) for a,b in zip(theta,reported_logits));high=[None]*len(groups);seen=set();maximum_error=0.;states=0
            adjacency=defaultdict(set);reverse=defaultdict(set)
            for u,v in g['condensation_edges']:adjacency[u].add(v);reverse[v].add(u)
            for result in map(json.loads,(directory/'component_partitions.jsonl').open()):
                labels=result['nodes'];assert not seen&set(labels);seen.update(labels);index={v:i for i,v in enumerate(labels)};n=len(labels);full=(1<<n)-1;trace={int(k):v for k,v in result['trace'].items()};assert 0 in trace and full in trace and len(trace)==result['states'];down=[];up=[]
                for v in labels:
                    for graph_edges,target in [(adjacency,down),(reverse,up)]:
                        reached={v};pending=[v]
                        while pending:
                            for other in graph_edges[pending.pop()]:
                                assert other in index
                                if other not in reached:reached.add(other);pending.append(other)
                        target.append(sum(1<<index[x] for x in reached))
                cache={};reachable=set();pending=[full]
                while pending:
                    free=pending.pop()
                    if free in reachable:continue
                    reachable.add(free);t=trace[free]
                    if t['kind']=='product':pending.extend(t['children'])
                    elif t['kind']=='branch':pending.extend([t['child_A'],t['child_B']])
                assert reachable==set(trace)
                for free in sorted(trace,key=int.bit_count):
                    t=trace[free]
                    if t['kind']=='empty':assert free==0;Z=Decimal(1);marg=[Decimal(0)]*n
                    elif t['kind']=='product':
                        children=t['children'];union=0
                        for part in children:assert part and not union&part and part!=free;union|=part
                        assert union==free
                        for u in labels:
                            for v in adjacency[u]:
                                if free>>index[u]&1 and free>>index[v]&1:assert any(part>>index[u]&1 and part>>index[v]&1 for part in children)
                        Z=math.prod(cache[c][0] for c in children);marg=[sum((cache[c][1][i] for c in children),Decimal()) for i in range(n)]
                    else:
                        assert t['kind']=='branch';i=t['vertex'];fa=up[i]&free;fb=down[i]&free;ca=free&~fa;cb=free&~fb;assert (t['forced_A'],t['forced_B'],t['child_A'],t['child_B'])==(fa,fb,ca,cb);za,ma=cache[ca];zb,mb=cache[cb];tilt=sum((theta[labels[j]] for j in range(n) if fb>>j&1),Decimal());factor=tilt.exp() if tilt else Decimal(1);wb=zb*factor;Z=za+wb;marg=[(za*ma[j]+wb*(Decimal(1) if fb>>j&1 else mb[j]))/Z for j in range(n)]
                    cache[free]=(Z,marg);z=ln2 if Z==2 else Z.ln();assert math.isclose(float(z),t['logZ'],rel_tol=1e-11,abs_tol=1e-9)
                    for a,b in zip(marg,t['marginals']):maximum_error=max(maximum_error,abs(float(a)-b));assert abs(float(a)-b)<=1e-9
                Z,marg=cache[full];assert math.isclose(float(Z.ln()),result['log_partition'],rel_tol=1e-11,abs_tol=1e-9)
                for i,v in enumerate(labels):assert high[v] is None;high[v]=marg[i];assert abs(float(marg[i])-raw_marginals[v])<=1e-9
                states+=len(trace)
            assert seen==set(range(len(groups))) and states==row['partition_subproblems'];stored={int(n):v for n,v in json.loads((directory/'expected_ledger_scaled.json').read_text()).items()};precise={};maximum_units=0
            for node in A.keys()|B.keys():
                # Independent owner-wise formula; no group delta shortcut.
                value=sum((1-high[component[n]] for n in A[node]-B[node]),Decimal(len(A[node]&B[node])))+sum((high[component[n]] for n in B[node]-A[node]),Decimal());quantized=int((value*SCALE).to_integral_value(rounding=ROUND_HALF_EVEN));assert value>=Decimal('-1e-50');assert abs(quantized-stored.get(node,0))<=1000;maximum_units=max(maximum_units,abs(quantized-stored.get(node,0)))
                if quantized:precise[node]=quantized
            assert all(precise.get(n,0)<=SCALE for n in safe) and all(precise.get(n,0)<=SCALE for n in g['eligible_resources']);path=directory/'high_precision_expected_ledger_scaled.json'
            with path.open('x') as f:json.dump(precise,f)
            bindings[str(path)]=sha(path);rows.append(dict(case=case,NETs=55300,connections=115572,partition_subproblems=states,maximum_high_precision_marginal_error=maximum_error,maximum_ledger_grid_difference_units=maximum_units,high_precision_mean_overuse_scaled=sum(max(0,v-SCALE*caps[n]) for n,v in precise.items())));print('JOINT_ENSEMBLE_ORIGINAL_BANKS_RECURRENCE_60DIGIT_AND_LEDGER_PASS',case,'grid_difference',maximum_units,flush=True)
    with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_ORIGINAL_BANKS_COMPLETE_RECURRENCES_HIGH_PRECISION_MARGINALS_AND_LEDGER_VERIFIED',rows=rows,bindings=bindings,scope='Full original candidate membership/coverage and independently60digit recurrences. Both original and high-precision ledgers must be scored for decision stability. Mean overuse is not expected overuse; no global legal-route or unseen prediction claim.'),f,indent=2)


if __name__=='__main__':main()
