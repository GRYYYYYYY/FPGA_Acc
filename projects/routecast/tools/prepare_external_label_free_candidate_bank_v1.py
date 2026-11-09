"""Bounded label-free complete-NET candidate harvesting and one-node avoidance.
Existing states/proposals precede cold labels. No metrics/native target route IO.
"""
import json,sys,time
from collections import defaultdict,Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from soft_demand_workspace_bridge_v1 import Search
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19';O=R/'experiments/prospective_external_family_label_free_bank_v1_2026-10-19';LIMIT=16

def forbidden(p):
    p=Path(p).resolve()
    return any(p.is_relative_to(D/x) for x in ('native','utility','specifications')) or (p.parent==D and 'comparison' in p.name)
def read(p):
    if forbidden(p):raise ValueError('target label input forbidden')
    return json.loads(Path(p).read_text())
def main():
    begin=time.perf_counter();O.mkdir(exist_ok=False);bp=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';bundle=read(bp);inputs={r['case']:r for r in bundle['rows']};paths=[Path(__file__).resolve(),bp];bindings={**closure([Path(__file__)])};providers=[]
    for width in (96,128,160):
        for episode in (1,2,3):
            case=f'w{width:03d}/episode_{episode:02d}';folder=D/'predictions'/case
            proofs=[folder/m/'complete_event_audit.json' for m in ('raw_min_on','native_retained_on')]
            providers.append(dict(case=case,available=all(p.exists() for p in proofs)))
            if all(p.exists() for p in proofs):paths.extend(proofs)
    for p in paths:bindings[str(p)]=sha(p)
    policy=dict(candidate_sources=['both complete warm initial states','both feedback round states','complete committed/rejected NET proposals only'],extra_generation='first at most16 mandatory-conflict unit nodes ascending RR ID; every forced NET ascending NET ID; one raw shortest shared-source tree with that node forbidden; same frozen perCID budgets',no_parameter_sweep=True,labels_opened=False,gate_changes=False,scope='Candidate coverage and necessary-capacity conflicts only, not forecast evaluation or a legal/native route.')
    (O/'protocol.json').write_text(json.dumps(dict(policy=policy,bindings=bindings,providers=providers),indent=2)+'\n');rows=[]
    for provider in providers:
        case=provider['case']
        if not provider['available']:rows.append(dict(case=case,status='UNAVAILABLE_SOURCE_BRANCH'));continue
        tick=time.perf_counter();info=inputs[case];ep=Path(info['endpoint']);meta=read(ep);graph,digest,nodes,fields,rc,queries=load_endpoints(ep);caps=fields['capacities'];slots={eid:i for i,eid in enumerate(fields['edge_ids'])};groups=defaultdict(dict)
        for q in queries:groups[q['net_id']][q['connection_id']]=q
        banks={net:[] for net in groups};seen={net:{} for net in groups};owned={net:[] for net in groups};frozen={};case_bindings={str(ep):sha(ep)}
        def admit(path):
            proof=read(path)
            if not proof.get('all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'):raise ValueError('complete provider audit required')
            for p,h in proof['bindings'].items():
                if forbidden(p):raise ValueError('provider contaminated by target evidence')
                if sha(p)!=h:raise ValueError('provider changed')
                case_bindings[p]=h
            case_bindings[str(path)]=sha(path)
        def add(recs,origin):
            if not recs:raise ValueError('empty candidate')
            net=recs[0]['net_id'];qs=groups[net];by={r['connection_id']:r for r in recs}
            if len(by)!=len(recs) or set(by)!=set(qs):raise ValueError('complete NET required')
            signature=tuple((cid,tuple(by[cid]['answer']['physical_edge_ids'])) for cid in sorted(by))
            if signature in seen[net]:return False
            parents={};union=set()
            for cid,r in by.items():
                q=qs[cid]
                if any(r[k]!=q[k] for k in q):raise ValueError('candidate endpoint')
                if r['budget_integer']!=frozen[cid]:raise ValueError('budget mismatch')
                u=q['source'];visited={u};value=rc.initial(u);edges=r['answer']['physical_edge_ids']
                for index,eid in enumerate(edges):
                    slot=slots[eid]
                    if not fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1]:raise ValueError('original arc')
                    v=fields['dest_ranks'][slot]
                    if v in visited or caps[v]<=0:raise ValueError('cycle/disabled node')
                    if index<len(edges)-1 and nodes[v].get('type') in ('SOURCE','SINK'):raise ValueError('interior terminal')
                    if nodes[v].get('type')!='SINK':
                        edge=(u,eid)
                        if v in parents and parents[v]!=edge:raise ValueError('NET parent conflict')
                        parents[v]=edge
                    value+=rc.increments[slot];visited.add(v);u=v
                if u!=q['sink'] or value!=r['answer']['delay'] or value>frozen[cid]:raise ValueError('RC budget')
                union.update(visited)
            seen[net][signature]=len(banks[net]);banks[net].append(dict(origin=origin,records=recs));owned[net].append(union);return True
        def frame(path,origin):
            p=Path(path);f=read(p);case_bindings[str(p)]=sha(p);parts=defaultdict(list)
            for r in f['records']:parts[r['net_id']].append(r)
            if set(parts)!=set(groups):raise ValueError('frame NET universe')
            for net,recs in sorted(parts.items()):add(recs,origin)
        warm_path=D/'predictions'/case/'warm/native_retained/initial.json';warm=read(warm_path);frozen={r['connection_id']:r['budget_integer'] for r in warm['records']};assert len(frozen)==len(queries)
        for method in ('raw_min_on','native_retained_on'):
            folder=D/'predictions'/case/method;admit(folder/'complete_event_audit.json');receipt=read(folder/'receipt.json');frame(folder/'initial.json',method+'/initial')
            for round_row in receipt['rounds']:
                frame(round_row['state_file'],method+'/round'+str(round_row['round_index']))
                for event in round_row['events']:
                    for key in ('records','rejected_records'):
                        if key in event:add(event[key],method+'/event/'+key)
        def conflicts():
            required=defaultdict(set)
            for net,options in owned.items():
                if not options:raise ValueError('empty NET bank')
                for n in set.intersection(*options):required[n].add(net)
            return [dict(node=n,capacity=caps[n],NETs=sorted(ns)) for n,ns in sorted(required.items()) if len(ns)>caps[n]]
        before=conflicts();before_count=sum(map(len,banks.values()));chosen=[r for r in before if r['capacity']==1][:LIMIT];searches=[];binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';contract=R/'experiments/soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';cv=read(contract);assert cv['bindings'][str(binary)]==sha(binary);case_bindings[str(contract)]=sha(contract);case_bindings.update(cv['bindings'])
        for conflict in chosen:
            taboo=conflict['node'];modified=dict(fields);modified['capacities']=list(caps);modified['capacities'][taboo]=0;search=Search(modified,rc,binary);search.prepare({},0)
            try:
                for net in conflict['NETs']:
                    qs=groups[net];source=next(iter(qs.values()))['source'];result=dict(node=taboo,net_id=net,status='NO_ADMITTED_CANDIDATE')
                    if source==taboo:result['reason']='FORBIDDEN_SOURCE';searches.append(result);continue
                    distance,parent,settled=search.search(source,{q['sink'] for q in qs.values()});bad=[cid for cid,q in qs.items() if q['sink'] not in settled or distance[q['sink']]>frozen[cid]]
                    if bad:result['rejected_CIDs']=bad;searches.append(result);continue
                    recs=[]
                    for cid,q in sorted(qs.items()):
                        u=q['sink'];edges=[];visited=set()
                        while u!=source:
                            assert u not in visited and u!=taboo;visited.add(u);u,slot=parent[u];edges.append(fields['edge_ids'][slot])
                        edges.reverse();recs.append(dict(q,budget_integer=frozen[cid],answer=dict(status='FOUND',physical_edge_ids=edges,delay=distance[q['sink']])))
                    added=add(recs,'new_raw_avoid_node_'+str(taboo));result.update(status='ADMITTED_NEW' if added else 'DUPLICATE',connections=len(recs));searches.append(result)
            finally:search.close()
        after=conflicts();out=O/case;out.mkdir(parents=True)
        with (out/'candidate_bank.jsonl').open('x') as f:
            for net in sorted(banks):f.write(json.dumps(dict(net_id=net,candidates=banks[net]),separators=(',',':'))+'\n')
        detail=dict(before_necessary_conflicts=before,after_necessary_conflicts=after,searches=searches);(out/'generation.json').write_text(json.dumps(detail,indent=2)+'\n')
        for p in (out/'candidate_bank.jsonl',out/'generation.json'):case_bindings[str(p)]=sha(p)
        if not all(not forbidden(p) and sha(p)==h for p,h in case_bindings.items()):raise ValueError('input drift/target contamination')
        row=dict(case=case,status='BOUNDED_LABEL_FREE_CANDIDATE_GENERATION_COMPLETE',NETs=len(banks),candidates_before=before_count,candidates_after=sum(map(len,banks.values())),necessary_conflicts_before=len(before),necessary_conflicts_after=len(after),selected_conflict_nodes=len(chosen),new_searches=len(searches),new_candidates=sum(s['status']=='ADMITTED_NEW' for s in searches),labels_opened=False,component_seconds=time.perf_counter()-tick)
        (out/'verification.json').write_text(json.dumps(dict(**row,bindings=case_bindings,scope=policy['scope']),indent=2)+'\n');rows.append(row);print('LABEL_FREE_BANK',json.dumps(row),flush=True)
    (O/'verification.json').write_text(json.dumps(dict(status='FIXED9_BOUNDED_LABEL_FREE_BANK_COMPONENT_TERMINAL',rows=rows,policy=policy,bindings={str(O/'protocol.json'):sha(O/'protocol.json')},total_component_seconds=time.perf_counter()-begin,scope='Six unavailable source cases retained. Candidate generation only; no SAT/selection, metric evaluation, native route or promotion. Upstream paid provider generation/audits excluded from component clock and still required for full accounting.'),indent=2)+'\n')
if __name__=='__main__':main()
