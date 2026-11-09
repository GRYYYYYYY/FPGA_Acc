"""One frozen core-guided expansion round, no labels or work-budget sweep."""
import json,sys,time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from soft_demand_workspace_bridge_v1 import Search
R=Path(__file__).resolve().parents[1];B=R/'experiments/prospective_external_family_label_free_bank_v1_2026-10-19';P=R/'experiments/prospective_external_family_choice_unit_provenance_v1_2026-10-19';O=R/'experiments/prospective_external_family_core_expansion_probe_v2_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
    O.mkdir(exist_ok=False);matrix=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};graph,digest,nodes,fields,rc,unused=load_endpoints(inputs['w160/episode_01']['endpoint']);caps=fields['capacities'];slots={e:i for i,e in enumerate(fields['edge_ids'])};binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';source_proof=B/'independent_verification_v1.json';a=read(source_proof);assert a['status']=='ALL3_LABEL_FREE_BANKS_XML_PATHS_BUDGETS_AND_NECESSARY_CONFLICTS_VERIFIED';assert all(sha(p)==h for p,h in a['bindings'].items());prov=read(P/'verification.json');assert all(sha(p)==h for p,h in prov['bindings'].items());bindings={**closure([Path(__file__)]),str(source_proof):sha(source_proof),str(P/'verification.json'):sha(P/'verification.json'),str(matrix):sha(matrix)}
    kernel_contract=R/'experiments/soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';kernel=read(kernel_contract);assert kernel['bindings'][str(binary)]==sha(binary);assert all(sha(p)==h for p,h in kernel['bindings'].items());bindings.update(kernel['bindings']);bindings[str(kernel_contract)]=sha(kernel_contract);bindings[str(binary)]=sha(binary)
    cases=[];data={}
    for episode in (1,2,3):
        case=f'w160/episode_{episode:02d}';bankfile=B/case/'candidate_bank.jsonl';bank={};ownership={};required=defaultdict(set)
        for line in bankfile.read_text().splitlines():
            d=json.loads(line);net=d['net_id'];bank[net]=d['candidates'];options=[]
            for candidate in d['candidates']:
                ns={r['source'] for r in candidate['records']}
                for r in candidate['records']:ns.update(fields['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
                options.append(ns)
            ownership[net]=options
            for n in set.intersection(*options):required[n].add(net)
        proof=read(P/f'episode_{episode:02d}.json');actions=[];seen=set()
        def action(net,taboo,kind):
            key=(net,tuple(sorted(taboo)))
            if key not in seen:seen.add(key);actions.append(dict(net_id=net,forbidden_nodes=list(key[1]),kind=kind))
        if proof['direct_mandatory_conflicts']:
            first=min(proof['direct_mandatory_conflicts'],key=lambda x:x['node'])
            for net in sorted(first['mandatory_NETs']):action(net,{first['node']},'DIRECT_CORE_OWNER_SINGLE_NODE_AVOID')
        else:
            for net in sorted({u['net_id'] for u in proof['negative_CHOICE_units']}):action(net,{n for n,owners in required.items() if caps[n]==1 and owners-{net}},'BLOCKED_NET_AVOID_ALL_FOREIGN_MANDATORY')
            for unit in proof['negative_CHOICE_units']:
                witness=unit['chosen_witness']
                for net in witness['mandatory_other_NETs']:action(net,{witness['node']},'BLOCKING_NET_AVOID_WITNESS_NODE')
        actions.sort(key=lambda x:(x['net_id'],x['kind'],x['forbidden_nodes']));cases.append(dict(case=case,actions=actions));data[case]=(bank,ownership);bindings[str(bankfile)]=sha(bankfile);bindings[str(P/f'episode_{episode:02d}.json')]=sha(P/f'episode_{episode:02d}.json')
    protocol=dict(policy='Exactly one supplied certified unit-propagation core per case, one expansion round only. First direct required-node conflict, or all negative-choice witness blockers plus foreign-mandatory avoidance for blockedNET. Deterministic sorted actions, one raw shared-source shortest tree each. No label, cost/threshold quota sweep or budget change.',cases=cases,unavailable_cases=[f'w{w:03d}/episode_{e:02d}' for w in (96,128) for e in (1,2,3)],bindings=bindings)
    (O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
    for spec in cases:
        tick=time.perf_counter();case=spec['case'];bank,ownership=data[case];before=sum(map(len,bank.values()));results=[];meta=read(inputs[case]['endpoint']);qs={q['connection_id']:q for q in meta['connections']}
        for number,action in enumerate(spec['actions']):
            net=action['net_id'];template={r['connection_id']:r for r in bank[net][0]['records']};budgets={cid:r['budget_integer'] for cid,r in template.items()};source=next(iter(template.values()))['source'];taboo=set(action['forbidden_nodes']);result=dict(action=number,net_id=net,kind=action['kind'],forbidden_node_count=len(taboo),status='NO_ADMITTED_CANDIDATE')
            if source in taboo:result['reason']='FORBIDDEN_SOURCE';results.append(result);continue
            modified=dict(fields);modified['capacities']=list(caps)
            for n in taboo:modified['capacities'][n]=0
            search=Search(modified,rc,binary);search.prepare({},0)
            try:
                dist,parent,settled=search.search(source,{q['sink'] for q in template.values()});bad=[cid for cid,q in template.items() if q['sink'] not in settled or dist[q['sink']]>budgets[cid]]
                if bad:result['unsettled_or_budget_failed_CIDs']=bad;results.append(result);continue
                recs=[];parents={};owned={source}
                for cid,old in sorted(template.items()):
                    q=qs[cid];u=q['sink'];edges=[];seen=set()
                    while u!=source:
                        assert u not in taboo and u not in seen;seen.add(u);u,slot=parent[u];edges.append(fields['edge_ids'][slot])
                    edges.reverse();value=rc.path(source,q['sink'],edges);assert value==dist[q['sink']]<=budgets[cid];u=source
                    for eid in edges:
                        slot=slots[eid];v=fields['dest_ranks'][slot]
                        if nodes[v].get('type')!='SINK':assert v not in parents or parents[v]==(u,eid);parents[v]=(u,eid)
                        owned.add(v);u=v
                    recs.append(dict(old,answer=dict(status='FOUND',physical_edge_ids=edges,delay=value)))
                assert not owned&taboo;signature=tuple((r['connection_id'],tuple(r['answer']['physical_edge_ids'])) for r in recs);old_signatures={tuple((r['connection_id'],tuple(r['answer']['physical_edge_ids'])) for r in sorted(c['records'],key=lambda x:x['connection_id'])) for c in bank[net]}
                if signature in old_signatures:result['status']='DUPLICATE'
                else:bank[net].append(dict(origin='core_probe_action_'+str(number),records=recs,forbidden_nodes=action['forbidden_nodes']));result['status']='ADMITTED_NEW'
            finally:search.close()
            results.append(result)
        out=O/case;out.mkdir(parents=True)
        with (out/'candidate_bank.jsonl').open('x') as f:
            for net in sorted(bank):f.write(json.dumps(dict(net_id=net,candidates=bank[net]),separators=(',',':'))+'\n')
        (out/'actions.json').write_text(json.dumps(results,indent=2)+'\n');row=dict(case=case,old_candidates=before,new_candidates=sum(r['status']=='ADMITTED_NEW' for r in results),actions=len(results),no_admitted=sum(r['status']=='NO_ADMITTED_CANDIDATE' for r in results),duplicates=sum(r['status']=='DUPLICATE' for r in results),component_seconds=time.perf_counter()-tick);rows.append(row);print('CORE_PROBE',row,flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (O/'verification.json').write_text(json.dumps(dict(status='FIXED_ONE_ROUND_CORE_GUIDED_CANDIDATE_PROBE_TERMINAL',bindings={str(O/'protocol.json'):sha(O/'protocol.json')},rows=rows,labels_opened=False,budgets_changed=False,scope='One conflict-driven generation probe only. No-admitted outcome is search/mask-specific, not general routing infeasibility. Merged bank requires independent validation and complete re-encoding/solving before any feasibility claim.'),indent=2)+'\n')
if __name__=='__main__':main()
