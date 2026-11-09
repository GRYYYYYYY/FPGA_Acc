"""Independently audit new completeNET paths and unchanged admitted bank prefix."""
import json,xml.etree.ElementTree as ET
from array import array
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];B=R/'experiments/prospective_external_family_blocker_release_v1_2026-10-19';D=R/'experiments/prospective_external_family_global_mask_probe_v2_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
    protocol=read(D/'protocol.json');assert all(sha(p)==h for p,h in protocol['bindings'].items());summary=read(D/'verification.json');matrix=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};first=read(inputs['w160/episode_01']['endpoint']);graph=Path(first['inputs']['graph']['path']);caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='node' and parent=='rr_nodes':
            assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));types.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
        elif e.tag=='switch' and parent=='switches':
            t=e.find('timing');assert all(Fraction(t.get(k,'0'))==0 for k in ('R','Cin','Cout','Cinternal'));value=Fraction(t.get('Tdel','0'))*10**18;assert value.denominator==1;weights[int(e.get('id'))]=value.numerator
        elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));switches.append(int(e.get('switch_id')))
        if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
        stack.pop()
    rows=[];bindings={str(p):sha(p) for p in [D/'protocol.json',D/'verification.json',B/'independent_verification_v1.json',graph,Path(__file__).resolve()]}
    for row in summary['rows']:
        case=row['case'];meta=read(inputs[case]['endpoint']);queries={q['connection_id']:q for q in meta['connections']};query_groups={}
        for cid,q in queries.items():query_groups.setdefault(q['net_id'],set()).add(cid)
        oldfile=B/case/'candidate_bank.jsonl';newfile=D/case/'candidate_bank.jsonl';old={x['net_id']:x['candidates'] for x in map(json.loads,oldfile.read_text().splitlines())};new={x['net_id']:x['candidates'] for x in map(json.loads,newfile.read_text().splitlines())};assert set(old)==set(new)
        spec=next(r for r in protocol['cases'] if r['case']==case);actions=spec['actions'];required=defaultdict(set)
        for net,options in old.items():
            owned_options=[]
            for candidate in options:
                owned={r['source'] for r in candidate['records']}
                for r in candidate['records']:owned.update(vs[eid] for eid in r['answer']['physical_edge_ids'])
                owned_options.append(owned)
            for node in set.intersection(*owned_options):required[node].add(net)
        cp=R/'experiments/prospective_external_family_blocker_release_cnf_v1_2026-10-19'/case/'encoding.json';cnf=read(cp);negative={-c[0] for c in cnf['clauses'] if len(c)==1 and c[0]<0};groups=defaultdict(set)
        for i,v in enumerate(cnf['variables'],1):
            if v['kind']=='CHOICE':groups[v['key'][0]].add(i)
        empty=sorted(net for net,options in groups.items() if options<=negative);assert spec['initial_empty_NETs']==empty
        expected={}
        def add(net,mask,kind):expected.setdefault((net,tuple(sorted(mask))),kind)
        conflicts=[(n,sorted(owners)) for n,owners in sorted(required.items()) if caps[n]==1 and len(owners)>1];assert spec['direct_conflicts']==len(conflicts)
        owned_options={};propagated=defaultdict(set)
        choice_vars={(v['key'][0],v['key'][1]):i for i,v in enumerate(cnf['variables'],1) if v['kind']=='CHOICE'}
        for net,options in old.items():
            sets=[];remaining=[]
            for index,candidate in enumerate(options):
                owned={r['source'] for r in candidate['records']}
                for r in candidate['records']:owned.update(vs[eid] for eid in r['answer']['physical_edge_ids'])
                sets.append(owned)
                if choice_vars[net,index] not in negative:remaining.append(owned)
            owned_options[net]=sets;assert remaining
            for node in set.intersection(*remaining):
                if caps[node]==1:propagated[node].add(net)
        conflicted={net for owners in propagated.values() if len(owners)>1 for net in owners};masks=defaultdict(set);blocked=defaultdict(set);relevant=defaultdict(set)
        for variable in sorted(negative):
            role=cnf['variables'][variable-1];assert role['kind']=='CHOICE';net,index=role['key'];found=False
            for node in owned_options[net][index]:
                if caps[node]!=1:continue
                for blocker in required[node]-{net}:
                    found=True;masks[blocker].add(node);blocked[blocker].add(variable)
                    if net in conflicted:relevant[blocker].add(variable)
            assert found
        winner=min(masks,key=lambda net:(-len(relevant[net]),-len(blocked[net]),net))
        add(winner,masks[winner],'MAX_CONFLICT_OPTION_INFLUENCE_UNION_MASK')
        wanted=sorted([dict(net_id=net,forbidden_nodes=list(mask),kind=kind) for (net,mask),kind in expected.items()],key=lambda x:(x['net_id'],x['kind'],x['forbidden_nodes']))
        assert actions==wanted;bindings[str(cp)]=sha(cp);count=paths=0
        for net,options in old.items():
            assert new[net][:len(options)]==options;budgets={r['connection_id']:r['budget_integer'] for r in options[0]['records']};qids=query_groups[net]
            for candidate in new[net][len(options):]:
                count+=1;records={r['connection_id']:r for r in candidate['records']};assert len(records)==len(candidate['records']) and set(records)==qids;number=int(candidate['origin'].rsplit('_',1)[1]);action=actions[number];assert action['net_id']==net and action['forbidden_nodes']==candidate['forbidden_nodes'];taboo=set(action['forbidden_nodes']);parents={}
                for cid,r in records.items():
                    q=queries[cid];assert all(q[k]==r[k] for k in q);assert r['budget_integer']==budgets[cid];u=q['source'];seen={u};assert types[u]=='SOURCE' and caps[u]>0 and u not in taboo;delay=0;edges=r['answer']['physical_edge_ids']
                    for index,eid in enumerate(edges):
                        assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and v not in taboo and caps[v]>0
                        if index<len(edges)-1:assert types[v] not in ('SOURCE','SINK')
                        if types[v]!='SINK':assert v not in parents or parents[v]==(u,eid);parents[v]=(u,eid)
                        seen.add(v);delay+=weights[switches[eid]];u=v
                    assert u==q['sink'] and types[u]=='SINK' and delay==r['answer']['delay']<=budgets[cid];paths+=1
        assert count==row['new_candidates'];rows.append(dict(case=case,new_candidates=count,new_connection_paths=paths,original_bank_prefix_unchanged=True,all_fixed_policy_actions_independently_reconstructed=True,all_original_XML_paths_parent_trees_budgets_and_masks_pass=True))
        for p in (oldfile,newfile,Path(inputs[case]['endpoint'])):bindings[str(p)]=sha(p)
        print('CORE_PROBE_INDEPENDENT_PATH_AUDIT',rows[-1],flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL_DOMINANT_UNION_MASK_CANDIDATES_INDEPENDENTLY_PHYSICALLY_VERIFIED',bindings=bindings,rows=rows,labels_opened=False,scope='Prevalidated old bank unchanged; new completeNET trees checked on originalXML exact RC and taboo masks. No joint capacity feasibility, target quality or native acceptance claim.'),indent=2)+'\n')
if __name__=='__main__':main()
