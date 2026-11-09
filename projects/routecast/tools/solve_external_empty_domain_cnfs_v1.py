"""One fixed bounded certified solve per candidate bank; no labels or tuning."""
import json,sys,time,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from certified_cnf_dependency_cdcl_v2 import solve
from verify_certified_cnf_dependency_cdcl_v1 import verify
from source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_empty_domain_cnf_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
    proof_path=D/'independent_structure_verification_v1.json';a=read(proof_path);assert a['status']=='ALL3_COMPLETE_NET_BANK_CNFS_INDEPENDENT_XML_ROLES_AND_CLAUSES_VERIFIED';assert all(sha(p)==h for p,h in a['bindings'].items());p=read(D/'protocol.json');assert p['policy']['max_solver_nodes']==1000
    out=D/'solve';out.mkdir(exist_ok=False);(out/'live_process.json').write_text(json.dumps(dict(pid=os.getpid(),max_nodes=1000))+'\n');bindings={**closure([Path(__file__)]),str(proof_path):sha(proof_path),str(D/'protocol.json'):sha(D/'protocol.json')};rows=[]
    for item in a['rows']:
        case=item['case'];path=D/case/'encoding.json';cnf=read(path);directory=out/case;directory.mkdir(parents=True);print('CERTIFIED_SOLVE_START',case,len(cnf['variables']),len(cnf['clauses']),flush=True);tick=time.perf_counter();result=solve(cnf['clauses'],len(cnf['variables']),max_nodes=1000);solve_seconds=time.perf_counter()-tick
        assert result['status'] in ('SAT','UNSAT','UNKNOWN_SEARCH_LIMIT')
        if result['status']=='UNKNOWN_SEARCH_LIMIT':assert result['visited_nodes']==1001
        rp=directory/'result.json';rp.write_text(json.dumps(result,separators=(',',':'))+'\n');verify_tick=time.perf_counter();verify(cnf['clauses'],result);verification_seconds=time.perf_counter()-verify_tick
        row=dict(case=case,status=result['status'],visited_nodes=result['visited_nodes'],rup_additions_verified=len(result['rup_additions']),proof_pass=result['status'] in ('SAT','UNSAT'),partial_additions_verified=True,solve_component_seconds=solve_seconds,RUP_or_model_verification_seconds=verification_seconds,bindings={str(path):sha(path),str(rp):sha(rp),str(proof_path):sha(proof_path)})
        (directory/'verification.json').write_text(json.dumps(row,indent=2)+'\n');bindings[str(directory/'verification.json')]=sha(directory/'verification.json');rows.append(row);(out/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('CERTIFIED_SOLVE_END',case,result['status'],result['visited_nodes'],len(result['rup_additions']),flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (out/'verification.json').write_text(json.dumps(dict(status='ALL3_FIXED_BOUND_CERTIFIED_FINITE_BANK_SOLVES_TERMINAL',bindings=bindings,rows=rows,max_nodes=1000,labels_opened=False,scope='Finite-bank logic only. Learned clauses independently RUP replayed; SAT CNF model is not yet an original-bank forest reconstruction; UNKNOWN is no feasibility result. No full graph infeasibility, estimator quality, native or complete time gain.'),indent=2)+'\n')
if __name__=='__main__':main()
