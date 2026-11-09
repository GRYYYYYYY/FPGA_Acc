"""Independent schedule/seed oracle and actual compiled rejected-tree nonmutation."""
import copy
import json
import resource
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from fractions import Fraction
from pathlib import Path
from compiled_quotient_model_factory_v2 import create,BINARY
from static_quotient_lower_bound_v1 import Graph as PythonGraph,Snapshot
from retained_criticality_tree_seed_v1 import seed as install
from criticality_retained_net_continue_primary_v1 import route
from criticality_retained_net_primary_v1 import route as stop_route
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha


class Spy:
    def __init__(self,graph):self.graph=graph;self.rejections=0
    def tree(self,source):
        t=self.graph.tree(source);original=t.expand
        def expand(*args):
            before=(dict(t.arrival),dict(t.parents));value=original(*args)
            if not value['committed']:
                assert before==(t.arrival,t.parents)
                self.rejections+=1
            return value
        t.expand=expand
        return t


def main():
    resource.setrlimit(resource.RLIMIT_AS,(512*2**20,512*2**20))
    counts=Counter();statuses=Counter();maximum=0
    for case in range(210):
        fanout=[1,2,15,16,17,32,64][case%7];n=fanout+3;unit=2**110 if case%4==0 else 1
        offsets=[0];dest=[];inc=[]
        for u in range(n):
            row=[(1,unit),(2,2*unit)] if u==0 else [(v,unit) for v in range(3,n)] if u in (1,2) else []
            for v,w in row:dest.append(v);inc.append(w)
            offsets.append(len(dest))
        fields=dict(row_offsets=offsets,dest_ranks=dest,capacities=[2]*n)
        eids=[1000+3*i for i in range(len(dest))];slots={e:i for i,e in enumerate(eids)}
        nodes=[]
        for i in range(n):
            node=ET.Element('node',type='SOURCE' if i==0 else 'SINK' if i>=3 else 'IPIN')
            ET.SubElement(node,'loc',layer='0',xlow=str(i*4),xhigh=str(i*4),ylow='0',yhigh='0');nodes.append(node)
        native=create(fields,inc,[0]*n,nodes,[0]*n,1);py=PythonGraph(native.lower)
        value=[Fraction(0),Fraction(1,2),Fraction(2,3),Fraction(1),Fraction(2**62-11,2**63-25)][case%5]
        prices=[0]*n;prices[1]=100*unit;snapshot=Snapshot(native.lower,prices)
        qs=[];old=[];criticalities={};ledger={i:1 for i in [0,1,*range(3,n)]}
        if case%3==0:ledger[1]=3
        elif case%3==2:
            for i in range(3,n,2):ledger[i]=3
        for cid,target in enumerate(range(3,n)):
            q=dict(connection_id=cid,net_id=56,source=0,sink=target);qs.append(q)
            old.append(dict(q,budget_integer=(2 if cid%3==0 else 4)*unit,answer=dict(physical_edge_ids=[eids[0],eids[offsets[1]+cid]])))
            criticalities[cid]=dict(net=56,source_rr=0,target_rr=target,criticality_numerator=value.numerator,criticality_denominator=value.denominator,local_sink_pin=cid)
        immutable=copy.deepcopy((qs,old,criticalities,ledger))
        try:
            spy=Spy(native);actual=route(spy,qs,old,criticalities,snapshot,eids,ledger,fields['capacities'],slots)
            t=py.tree(0);kept={};imports=[]
            if fanout>=16:
                for q,rec in zip(qs,old):
                    if all(ledger.get(i,0)<=2 for i in (0,1,q['sink'])):
                        path=[slots[e] for e in rec['answer']['physical_edge_ids']];imports.append((q['sink'],path,rec['budget_integer']));kept[q['connection_id']]=path
            install(t,imports);expected=[];attempts={};settled=set();rejected=[]
            for q in qs:
                cid=q['connection_id']
                if cid in kept:
                    settled.add(q['sink']);attempts[cid]=old[cid]['answer']['physical_edge_ids']
                    expected.append(dict(connection_id=cid,status='RETAINED_CLEAN_BRANCH',committed=True,raw=t.arrival[q['sink']],path_slots=tuple(kept[cid])))
            for q in qs:
                cid=q['connection_id']
                if cid in kept:continue
                before=(dict(t.arrival),dict(t.parents));result=t.expand(q['sink'],value,snapshot,old[cid]['budget_integer']);expected.append(dict(connection_id=cid,**result))
                if result['committed']:
                    settled.add(q['sink']);attempts[cid]=[eids[i] for i in result['path_slots']]
                else:
                    assert before==(t.arrival,t.parents)
                    rejected.append(dict(connection_id=cid,status=result['status'],raw=result.get('raw'),physical_edge_ids=[eids[i] for i in result['path_slots']] if 'path_slots' in result else None));attempts[cid]=None
            assert actual['search_results']==expected and actual['parents']==t.parents and actual['settled']==settled
            assert actual['rejected_expansions']==rejected
            assert actual['attempts']==[dict(connection_id=q['connection_id'],physical_edge_ids=attempts[q['connection_id']]) for q in qs]
            assert actual['search_calls']==fanout-len(kept) and actual['retained_connection_ids']==sorted(kept)
            assert actual['first_failed_connection_id']==(rejected[0]['connection_id'] if rejected else None)
            assert actual['complete']==all(q['sink'] in settled and t.arrival[q['sink']]<=old[q['connection_id']]['budget_integer'] for q in qs)
            control=stop_route(native,qs,old,criticalities,snapshot,eids,ledger,fields['capacities'],slots)
            if actual['search_calls']>control['search_calls']:counts['more_queries_than_stop_control']+=1
            nonretained=[x for x in expected if x['status']!='RETAINED_CLEAN_BRANCH']
            if any(not a['committed'] and any(b['committed'] for b in nonretained[i+1:]) for i,a in enumerate(nonretained)):counts['rejection_then_later_success_NETs']+=1
            counts['cases']+=1;counts['queries']+=actual['search_calls'];counts['rejected_expand_nonmutation']+=spy.rejections
            counts['retained_branches']+=len(kept)
            for x in expected:statuses[x['status']]+=1;maximum=max(maximum,x.get('objective_numerator',0).bit_length())
            assert (qs,old,criticalities,ledger)==immutable
        finally:native.close()
    assert counts['cases']==210 and counts['more_queries_than_stop_control'] and counts['rejection_then_later_success_NETs'] and counts['retained_branches'] and counts['rejected_expand_nonmutation'] and maximum>160
    # Prefix validation and retained-seed code are copied verbatim from the control.
    original=(R/'tools/criticality_retained_net_primary_v1.py').read_text().split(' for _,_,cid,q,value in sorted(ordered):')[0]
    candidate=(R/'tools/criticality_retained_net_continue_primary_v1.py').read_text().split(' rejected=[]')[0]
    assert original.split('\n',1)[1]==candidate.split('\n',1)[1]
    out=R/'experiments/continue_primary_contract_v1_2026-10-17';out.mkdir()
    bindings=closure([Path(__file__),R/'tools/criticality_retained_net_continue_primary_v1.py']);bindings[str(BINARY)]=sha(BINARY)
    prereg=R/'experiments/neuron_continue_after_rejection_prereg_v1_2026-10-17/protocol.json';bindings[str(prereg)]=sha(prereg)
    proof=dict(all_pass=True,bindings=bindings,counts=dict(counts),statuses=dict(statuses),maximum_objective_bits=maximum,independent_all_query_reference_parity=True,compiled_rejected_expansion_tree_nonmutation=True,original_identity_order_validation_and_retained_seed_prefix_unchanged=True,failed_paths_separate_from_committed_parent_and_attempt_maps=True,original_inputs_unchanged=True,full_XML_fixture_and_independent_event_auditor_still_required=True,new_neuron_model_submitted=False)
    (out/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='bindings'},indent=2))


if __name__=='__main__':main()
