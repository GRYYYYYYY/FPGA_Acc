"""Freeze full finite-bank CNF; no target labels or candidate selection."""
import json,sys,time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from whole_NET_bank_cnf_v1 import encode
R=Path(__file__).resolve().parents[1];B=R/'experiments/prospective_external_family_blocker_release_v1_2026-10-19';O=R/'experiments/prospective_external_family_blocker_release_cnf_v1_2026-10-19'
def main():
    O.mkdir(exist_ok=False);bp=B/'independent_verification_v1.json';proof=json.loads(bp.read_text());assert proof['status']=='ALL_BLOCKER_RELEASE_NEW_CANDIDATES_INDEPENDENTLY_PHYSICALLY_VERIFIED';assert all(sha(p)==h for p,h in proof['bindings'].items());matrix=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in json.loads(matrix.read_text())['rows']};provider=json.loads((B/'verification.json').read_text());provider['rows']=[dict(case=c,status='UNAVAILABLE_SOURCE_BRANCH') for c in json.loads((B/'protocol.json').read_text())['unavailable_cases']]+[dict(r,status='CORE_PROBE_BANK_READY') for r in provider['rows']];bindings={**closure([Path(__file__)]),str(bp):sha(bp),str(matrix):sha(matrix)}
    contract=R/'experiments/whole_NET_bank_cnf_contract_v1_2026-10-19/verification.json';bindings[str(contract)]=sha(contract)
    policy=dict(max_solver_nodes=1000,solver='certified_cnf_dependency_cdcl_v2',proof_checker='verify_certified_cnf_dependency_cdcl_v1',no_work_bound_sweep=True,semantics='Exactly one prevalidated complete-NET tree; exact unit capacity constraints; all used nonunit nodes must have invariant owner sets and fit capacity before omission.',failure_scope='Six source-unavailable cases retained. Unknown limit is no feasibility conclusion. SAT requires direct original-bank reconstruction; UNSAT only this finite bank.',labels_opened=False)
    (O/'protocol.json').write_text(json.dumps(dict(policy=policy,bindings=bindings),indent=2)+'\n');rows=[];context=None
    for row in provider['rows']:
        case=row['case']
        if row['status']=='UNAVAILABLE_SOURCE_BRANCH':rows.append(dict(case=case,status='UNAVAILABLE_SOURCE_BRANCH'));continue
        tick=time.perf_counter();ep=Path(inputs[case]['endpoint'])
        if context is None:context=load_endpoints(ep)
        graph,digest,nodes,fields,rc,unused=context;meta=json.loads(ep.read_text());assert meta['graph_sha256']==digest;slots={e:i for i,e in enumerate(fields['edge_ids'])};bankfile=B/case/'candidate_bank.jsonl';bank={}
        for line in bankfile.read_text().splitlines():
            d=json.loads(line);assert d['net_id'] not in bank;options=[]
            for candidate in d['candidates']:
                owned=set()
                for r in candidate['records']:owned.add(r['source']);owned.update(fields['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
                options.append(owned)
            bank[d['net_id']]=options
        result=encode(bank,fields['capacities']);directory=O/case;directory.mkdir(parents=True);p=directory/'encoding.json';p.write_text(json.dumps(result,separators=(',',':'))+'\n')
        with (directory/'problem.cnf').open('x') as f:
            f.write(f"p cnf {len(result['variables'])} {len(result['clauses'])}\n")
            for clause in result['clauses']:f.write(' '.join(map(str,clause))+' 0\n')
        record=dict(case=case,status='CNF_PREPARED_NOT_SOLVED',NETs=len(bank),choice_variables=sum(v['kind']=='CHOICE' for v in result['variables']),owner_variables=sum(v['kind']=='OWNER' for v in result['variables']),clauses=len(result['clauses']),mandatory_unit_conflicts=len(result['mandatory_unit_conflicts']),constant_nonunit_resources=len(result['constant_nonunit_resources']),encoding_seconds=time.perf_counter()-tick,bindings={str(q):sha(q) for q in [ep,graph,bankfile,p,directory/'problem.cnf',bp,O/'protocol.json']})
        (directory/'verification.json').write_text(json.dumps(record,indent=2)+'\n');rows.append(record);print('FINITE_BANK_CNF',json.dumps({k:v for k,v in record.items() if k!='bindings'}),flush=True)
    (O/'verification.json').write_text(json.dumps(dict(status='FIXED9_COMPLETE_NET_BANK_CNFS_PREPARED',rows=rows,policy=policy,bindings={str(O/'protocol.json'):sha(O/'protocol.json')},scope='Logical encoding only; physical/budget bank audit inherited. No solver result, selected route or scientific gate gain.'),indent=2)+'\n')
if __name__=='__main__':main()
