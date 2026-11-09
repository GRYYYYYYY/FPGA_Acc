"""Complete-bank joint distribution, frozen learned context, no new target access."""
import json,math,time,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from weighted_closed_state_marginals_v1 import calculate

R=Path(__file__).resolve().parents[1]
SCALE=10**12


def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2)


def main():
    pp=R/'experiments/mmc_joint_candidate_ensemble_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());out=R/'experiments/mmc_joint_candidate_ensemble_v1_2026-10-19';out.mkdir(exist_ok=False)
    source=R/'experiments/mmc_resource_probability_development_v1_2026-10-19';sp=source/'receipt.json';src=json.loads(sp.read_text());vp=source/'independent_verification_v1.json';v=json.loads(vp.read_text());assert v['status']=='ALL6_TRAIN_ONLY_RESOURCE_COUNTS_EXACT_PROBABILITIES_CLOSED_CHOICES_AND_LEDGER_VERIFIED' and v['bindings'][str(sp)]==sha(sp)
    context=R/'experiments/mmc_resource_context_v1_2026-10-19';ctx=json.loads((context/'receipt.json').read_text());nodepath=context/'CHANNEL_ids.u32';assert ctx['bindings'][str(nodepath)]==sha(nodepath);nodes=array('I');nodes.frombytes(nodepath.read_bytes());channel=set(nodes);assert len(channel)==258720
    graph=next(Path(p) for p in ctx['bindings'] if p.endswith('rr_graph.xml'));assert ctx['bindings'][str(graph)]==sha(graph);caps=array('I');stack=[]
    class Done(Exception):pass
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':assert int(a['id'])==len(caps);caps.append(int(a['capacity']))
        stack.append(tag)
    def closing(tag):
        assert stack.pop()==tag
        if tag=='rr_nodes':raise Done()
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    try:
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    except Done:pass
    bindings={str(p):sha(p) for p in [pp,sp,vp,nodepath,graph,Path(__file__).resolve(),R/'tools/weighted_closed_state_marginals_v1.py']};ownerroot=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';lineagep=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';lineage=json.loads(lineagep.read_text());bindings[str(lineagep)]=sha(lineagep);rows=[]
    for case in plan['cases']:
        begin=time.perf_counter();directory=out/case;directory.mkdir();gp=ownerroot/case/'graph.json';bp=ownerroot/case/'banks.jsonl';mp=source/case/'history_A_B_prefix_direction_segment/model.json';cp=context/(case+'.u16')
        for p in [gp,bp,mp]:assert plan['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p)
        assert src['bindings'][str(cp)]==sha(cp);bindings[str(cp)]=sha(cp);codes=array('H');codes.frombytes(cp.read_bytes());code=dict(zip(nodes,codes));m=json.loads(mp.read_text());assert case not in m['training_cases'] and m['with_prefix'];logodds=[math.log(s+1)-math.log(n-s+1) for n,s in zip(m['counts'],m['occupied'])]
        g=json.loads(gp.read_text());groups=g['components'];component={net:i for i,c in enumerate(groups) for net in c};banks={x['net_id']:x for x in map(json.loads,bp.open())};assert set(banks)==set(component) and len(banks)==55300
        item=next(x for x in lineage['cases'] if x['case']==case)
        for key in ['candidate_A','candidate_B','endpoint','candidate_B_physical_proof']:
            p=Path(item[key]);assert lineage['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p)
        A=defaultdict(set);B=defaultdict(set)
        for net,b in banks.items():
            for node in b['A']:A[node].add(net)
            for node in b['B']:B[node].add(net)
        safe={n for n in channel if len(A[n])<=1 and len(B[n])<=1};delta=defaultdict(Counter)
        for n in safe:
            for net in B[n]:delta[component[net]][code[n]]+=1
            for net in A[n]:delta[component[net]][code[n]]-=1
        logits=[math.fsum(value*logodds[k] for k,value in delta[i].items() if value) for i in range(len(groups))];adj=defaultdict(set);forward=defaultdict(list)
        for u,w in g['condensation_edges']:adj[u].add(w);adj[w].add(u);forward[u].append(w)
        seen=set();weak=[]
        for i in range(len(groups)):
            if i in seen:continue
            part=[];pending=[i];seen.add(i)
            while pending:
                u=pending.pop();part.append(u)
                for w in adj[u]:
                    if w not in seen:seen.add(w);pending.append(w)
            weak.append(sorted(part))
        marg=[None]*len(groups);state_count=0;tick=time.perf_counter();tracepath=directory/'component_partitions.jsonl'
        with tracepath.open('x') as f:
            for part in weak:
                edges=[(u,w) for u in part for w in forward[u]];result=calculate({i:logits[i] for i in part},edges);state_count+=result['states']
                for i,p in result['marginals'].items():assert marg[i] is None;marg[i]=p
                f.write(json.dumps(result,separators=(',',':'))+'\n')
        infer_seconds=time.perf_counter()-tick;assert all(p is not None and -1e-12<=p<=1+1e-12 for p in marg)
        assert all(marg[u]<=marg[w]+1e-10 for u,w in g['condensation_edges']);expected={};maximum_rounding=0.
        for node in A.keys()|B.keys():
            changes=Counter(component[n] for n in B[node]);changes.subtract(component[n] for n in A[node]);mean=math.fsum([float(len(A[node]))]+[v*marg[i] for i,v in changes.items() if v]);assert mean>=-1e-10
            quantized=round(mean*SCALE);assert quantized>=0
            if quantized:expected[node]=quantized
            maximum_rounding=max(maximum_rounding,abs(mean-quantized/SCALE))
        assert all(expected.get(n,0)<=SCALE for n in safe) and all(expected.get(n,0)<=SCALE for n in g['eligible_resources'])
        save(directory/'component_logits.json',logits);save(directory/'component_marginals.json',marg);save(directory/'expected_ledger_scaled.json',expected);deltafile=directory/'component_category_deltas.jsonl'
        with deltafile.open('x') as f:
            for i in range(len(groups)):
                values={k:v for k,v in delta[i].items() if v}
                if values:f.write(json.dumps(dict(component=i,deltas=values),separators=(',',':'))+'\n')
        rows.append(dict(case=case,NETs=len(banks),connections=115572,SCCs=len(groups),weak_components=len(weak),largest_weak_component=max(map(len,weak)),partition_subproblems=state_count,safe_CHANNELs=len(safe),excluded_CHANNELs=len(channel-safe),expected_ledger_scale=SCALE,mean_demand_overuse_scaled=sum(max(0,v-SCALE*caps[n]) for n,v in expected.items()),maximum_resource_rounding_error=maximum_rounding,partition_seconds=infer_seconds,case_component_seconds=time.perf_counter()-begin,eligible_for_legal_route_commit=False))
        for p in [tracepath,directory/'component_logits.json',directory/'component_marginals.json',directory/'expected_ledger_scaled.json',deltafile]:bindings[str(p)]=sha(p)
        print('JOINT_CANDIDATE_ENSEMBLE',case,'partition_states',state_count,'seconds',infer_seconds,'mean_overuse',rows[-1]['mean_demand_overuse_scaled']/SCALE,flush=True)
    save(out/'receipt.json',dict(status='ALL3_FROZEN_COMPLETE_BANK_JOINT_ENSEMBLES_PRODUCED',rows=rows,bindings=bindings,target_labels_read=False,independent_verification_pending=True,scope=plan['scope']))


if __name__=='__main__':main()
