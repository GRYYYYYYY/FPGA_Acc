"""Independently decode context codes; prefix features come from original N rows."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_resource_context_v1_2026-10-19';rp=root/'receipt.json';d=json.loads(rp.read_text());assert d['status']=='ALL3_LABEL_FREE_RESOURCE_CONTEXT_CODES_PRODUCED' and d['target_final_labels_read'] is False and all(sha(p)==h for p,h in d['bindings'].items())
    domain=json.loads((root/'domain.json').read_text());assert domain['byteorder']==sys.byteorder;nodes=array('I');nodes.frombytes((root/'CHANNEL_ids.u32').read_bytes());assert nodes.itemsize==4 and len(nodes)==len(set(nodes))==258720
    graph=next(Path(p) for p in d['bindings'] if p.endswith('rr_graph.xml'));expected={};stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
            if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
                assert int(e.get('capacity'))==1;seg=e.find('segment');expected[int(e.get('id'))]=(e.get('type'),int(seg.get('segment_id')) if seg is not None else -1)
            stack[-2].remove(e);e.clear()
        if e.tag=='rr_nodes':break
        stack.pop()
    assert list(nodes)==sorted(expected);groups=sorted(set(expected.values()));assert groups==list(map(tuple,domain['groups'])) and len(groups)==4
    prior=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';old={int(n):v for n,v in json.loads(prior.read_text())['ledger'].items()};prefix=R/'experiments/mmc_native_first_iteration_v1_2026-10-18';physical=json.loads((prefix/'physical_and_budget_verification_v1.json').read_text());identity=json.loads((prefix/'input_identity_verification_v1.json').read_text());pp=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());rows=[]
    for item in plan['cases']:
        case=item['case'];A,B=[{int(n):v for n,v in json.loads(Path(item[key]).read_text())['ledger'].items()} for key in ['candidate_A','candidate_B']];codes=array('H');codes.frombytes((root/(case+'.u16')).read_bytes());assert codes.itemsize==2 and len(codes)==len(nodes)
        state=prefix/case/'states/round_1.tsv';assert physical['bindings'][str(state)]==sha(state);occupancy={};header=None;count=0
        for line in state.open():
            x=line.split()
            if x[0]=='H':header=x
            elif x[0]=='N':
                n,occ,cap=map(int,x[1:4]);assert n==count and occ>=0;count+=1
                if n in expected:assert cap==1;occupancy[n]=occ
        assert header==['H','1','0','0'] and count==904438 and set(occupancy)==set(expected)
        assert next(x for x in identity['cases'] if x['case']==case)['native_executed_inputs_equal_current_staged_target']
        for n,code in zip(nodes,codes):
            group=code%4;q=code//4;early=q%3;q//=3;afterB=q%3;q//=3;afterA=q%3;past=q//3
            assert (past,afterA,afterB,early,groups[group])==(old.get(n,0),min(2,A.get(n,0)),min(2,B.get(n,0)),min(2,occupancy[n]),expected[n])
        rows.append(dict(case=case,resources_verified=len(nodes),prefix_N_rows_verified=count));print('RESOURCE_CONTEXT_ORIGINAL_XML_AND_PREFIX_N_ROWS_PASS',case,flush=True)
    with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_776160_CONTEXT_CODES_DOMAIN_AND_ORIGINAL_PREFIX_N_OCCUPANCIES_VERIFIED',rows=rows,bindings={str(p):sha(p) for p in [rp,root/'protocol.json',Path(__file__).resolve()]},scope='Independent graph grouping and original snapshot N occupancy decoding, no final target labels, no fitting or new route jobs. Prefix budget/quality failures remain; context never treated as legal candidate.'),f,indent=2)


if __name__=='__main__':main()
