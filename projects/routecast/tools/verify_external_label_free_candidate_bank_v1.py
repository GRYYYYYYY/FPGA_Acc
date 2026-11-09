"""Independent original-XML integer/Fraction audit of every complete NET option."""
import json,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19';O=R/'experiments/prospective_external_family_label_free_bank_v1_2026-10-19'
def read(p):
    p=Path(p).resolve()
    if any(p.is_relative_to(D/x) for x in ('native','utility','specifications')):raise ValueError('target labels forbidden')
    return json.loads(p.read_text())
def main():
    vp=O/'verification.json';proof=read(vp);bp=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(bp)['rows']};ep=read(inputs['w160/episode_01']['endpoint']);graph=Path(ep['inputs']['graph']['path']);caps=array('I');kinds=[];us=array('I');vs=array('I');switch=array('I');weights={};stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='node' and parent=='rr_nodes':
            assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
        elif e.tag=='switch' and parent=='switches':
            t=e.find('timing');assert all(Fraction(t.get(k,'0'))==0 for k in ('R','Cin','Cout','Cinternal'));w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1;weights[int(e.get('id'))]=w.numerator
        elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));switch.append(int(e.get('switch_id')))
        if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
        stack.pop()
    bindings={str(p):sha(p) for p in [vp,bp,graph,Path(__file__).resolve()]};rows=[]
    for item in proof['rows']:
        if item['status']=='UNAVAILABLE_SOURCE_BRANCH':continue
        case=item['case'];p=O/case/'candidate_bank.jsonl';meta=read(inputs[case]['endpoint']);assert meta['graph_sha256']==sha(graph);groups=defaultdict(dict)
        for q in meta['connections']:groups[q['net_id']][q['connection_id']]=q
        warm_path=D/'predictions'/case/'warm/native_retained/initial.json';warm=read(warm_path);budgets={r['connection_id']:r['budget_integer'] for r in warm['records']};seen=set();required_before=defaultdict(set);required_after=defaultdict(set);count=new=connections=0
        for line in p.read_text().splitlines():
            bank=json.loads(line);net=bank['net_id'];assert net in groups and net not in seen;seen.add(net);frequency=Counter();frequency_before=Counter();old_count=0;signatures=set()
            for candidate in bank['candidates']:
                count+=1;isnew=candidate['origin'].startswith('new_raw_avoid_node_');new+=isnew;parents={};owner=set();records={r['connection_id']:r for r in candidate['records']};assert len(records)==len(candidate['records']) and set(records)==set(groups[net]);signature=[]
                for cid,r in sorted(records.items()):
                    q=groups[net][cid];assert all(q[k]==r[k] for k in q);assert r['budget_integer']==budgets[cid];u=q['source'];assert kinds[u]=='SOURCE' and caps[u]>0;visited={u};delay=0;edges=r['answer']['physical_edge_ids'];signature.append((cid,tuple(edges)))
                    for index,eid in enumerate(edges):
                        assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in visited and caps[v]>0
                        if index<len(edges)-1:assert kinds[v] not in ('SOURCE','SINK')
                        if kinds[v]!='SINK':
                            incoming=(u,eid);assert v not in parents or parents[v]==incoming;parents[v]=incoming
                        delay+=weights[switch[eid]];visited.add(v);u=v
                    assert u==q['sink'] and kinds[u]=='SINK' and delay==r['answer']['delay']<=budgets[cid];owner.update(visited);connections+=1
                signature=tuple(signature);assert signature not in signatures;signatures.add(signature)
                if isnew:assert int(candidate['origin'].rsplit('_',1)[1]) not in owner
                else:frequency_before.update(owner);old_count+=1
                frequency.update(owner)
            assert old_count>0
            for n,k in frequency.items():
                if k==len(bank['candidates']):required_after[n].add(net)
            for n,k in frequency_before.items():
                if k==old_count:required_before[n].add(net)
        assert seen==set(groups) and count==item['candidates_after'] and new==item['new_candidates'] and count-new==item['candidates_before']
        generation=read(O/case/'generation.json')
        for label,required in [('before',required_before),('after',required_after)]:
            expected=[dict(node=n,capacity=caps[n],NETs=sorted(nets)) for n,nets in sorted(required.items()) if len(nets)>caps[n]];assert expected==generation[label+'_necessary_conflicts']
        for q in [p,Path(inputs[case]['endpoint']),warm_path,O/case/'generation.json']:bindings[str(q)]=sha(q)
        rows.append(dict(case=case,complete_NET_candidates=count,new_avoidance_candidates=new,connection_path_instances=connections,all_original_XML_arcs_parent_trees_and_budgets_pass=True,both_necessary_conflict_sets_recomputed=True));print('INDEPENDENT_LABEL_FREE_BANK_PASS',rows[-1],flush=True)
    assert len(rows)==3 and all(sha(p)==h for p,h in bindings.items())
    (O/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_LABEL_FREE_BANKS_XML_PATHS_BUDGETS_AND_NECESSARY_CONFLICTS_VERIFIED',bindings=bindings,rows=rows,labels_opened=False,scope='Original XML/Fraction exact path and shared-parent audits, taboo-node avoidance and Counter-frequency required-node reconstruction. Does not prove joint candidate selection, legal/native acceptance or forecast/native utility gains.'),indent=2)+'\n')
if __name__=='__main__':main()
