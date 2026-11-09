"""Restore concrete mandatory-owner provenance behind simplified CHOICE units."""
import json,sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];B=R/'experiments/prospective_external_family_label_free_bank_v1_2026-10-19';C=R/'experiments/prospective_external_family_label_free_cnf_v1_2026-10-19';O=R/'experiments/prospective_external_family_choice_unit_provenance_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
    O.mkdir(exist_ok=False);matrix=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};graph,digest,nodes,fields,rc,unused=load_endpoints(inputs['w160/episode_01']['endpoint']);slots={e:i for i,e in enumerate(fields['edge_ids'])};caps=fields['capacities'];rows=[];bindings={str(matrix):sha(matrix),str(Path(__file__).resolve()):sha(__file__)}
    for episode in (1,2,3):
        case=f'w160/episode_{episode:02d}';bp=B/case/'candidate_bank.jsonl';bank={};required=defaultdict(set)
        for line in bp.read_text().splitlines():
            d=json.loads(line);net=d['net_id'];options=[]
            for c in d['candidates']:
                owned={r['source'] for r in c['records']}
                for r in c['records']:owned.update(fields['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
                options.append(owned)
            bank[net]=options
            for n in set.intersection(*options):required[n].add(net)
        cp=C/case/'encoding.json';cnf=read(cp);sp=C/'supports'/(case.replace('/','_')+'.json');support=read(sp);units=[];direct=[]
        for clause in support['clauses']:
            if not clause:
                for conflict in cnf['mandatory_unit_conflicts']:
                    n=conflict['node'];owners=conflict['NETs'];assert caps[n]==1 and len(owners)>1
                    assert all(all(n in option for option in bank[net]) for net in owners);direct.append(dict(node=n,mandatory_NETs=owners,type=nodes[n].get('type')))
            elif len(clause)==1 and clause[0]<0:
                x=-clause[0];v=cnf['variables'][x-1];assert v['kind']=='CHOICE';net,index=v['key'];witnesses=[]
                for n in sorted(bank[net][index]):
                    others=required[n]-{net}
                    if caps[n]==1 and others:
                        assert len(required[n])==1
                        for owner in sorted(others):assert all(n in option for option in bank[owner])
                        witnesses.append(dict(node=n,type=nodes[n].get('type'),mandatory_other_NETs=sorted(others)))
                assert witnesses;units.append(dict(variable=x,net_id=net,option=index,witnesses=witnesses,chosen_witness=witnesses[0]))
        result=dict(case=case,negative_CHOICE_units=units,direct_mandatory_conflicts=direct,scope='Exact original-bank provenance of initial CNF units. Mandatory ownership is limited to this bank, not a global graph reachability claim.')
        p=O/f'episode_{episode:02d}.json';p.write_text(json.dumps(result,indent=2)+'\n')
        for q in (bp,cp,sp,p,Path(inputs[case]['endpoint'])):bindings[str(q)]=sha(q)
        rows.append(dict(case=case,direct_conflicts=len(direct),negative_units=len(units),blocked_NETs=sorted({u['net_id'] for u in units}),chosen_witnesses=[dict(net_id=u['net_id'],option=u['option'],**u['chosen_witness']) for u in units]));print('UNIT_RESOURCE_PROVENANCE',json.dumps(rows[-1]),flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (O/'verification.json').write_text(json.dumps(dict(status='ALL3_CNF_SUPPORT_CAPACITY_UNITS_HAVE_CONCRETE_ORIGINAL_BANK_WITNESSES',bindings=bindings,rows=rows,labels_opened=False),indent=2)+'\n')
if __name__=='__main__':main()
