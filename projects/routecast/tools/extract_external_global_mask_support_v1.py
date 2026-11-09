"""Extract independently RUP-replayable support subsets of fixed finite banks."""
import json
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from cnf_rup_support_indexed_v1 import extract
from verify_certified_cnf_dependency_cdcl_v1 import verify
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_global_mask_cnf_v1_2026-10-19'
def main():
    sp=D/'solve/verification.json';summary=json.loads(sp.read_text());assert summary['status']=='ALL3_FIXED_BOUND_CERTIFIED_FINITE_BANK_SOLVES_TERMINAL';O=D/'supports';O.mkdir(exist_ok=False);rows=[];bindings={str(sp):sha(sp),str(Path(__file__).resolve()):sha(__file__)}
    for row in summary['rows']:
        assert row['status']=='UNSAT';case=row['case'];cp=D/case/'encoding.json';rp=D/'solve'/case/'result.json';cnf=json.loads(cp.read_text());result=json.loads(rp.read_text());support=extract(cnf['clauses'],result);reduced=dict(status='UNSAT',model=None,rup_additions=support['rup_additions']);verify(support['clauses'],reduced)
        variables={abs(x) for c in support['clauses'] for x in c};roles={n:cnf['variables'][n-1] for n in sorted(variables)};nets=set();resources=set()
        for role in roles.values():
            if role['kind']=='CHOICE':nets.add(role['key'][0])
            elif role['kind']=='OWNER':resources.add(role['key'][0]);nets.add(role['key'][1])
            else:raise ValueError('unknown role')
        certificate=dict(case=case,original_clause_indices=support['original_indices'],clauses=support['clauses'],rup_additions=support['rup_additions'],roles=roles,contains_original_empty_clause=[] in support['clauses'],static_mandatory_conflicts=cnf['mandatory_unit_conflicts'] if [] in support['clauses'] else [])
        p=O/(case.replace('/','_')+'.json');p.write_text(json.dumps(certificate,indent=2)+'\n');bindings.update({str(cp):sha(cp),str(rp):sha(rp),str(p):sha(p)})
        record=dict(case=case,support_clauses=len(support['clauses']),support_variables=len(variables),NETs_in_variable_roles=len(nets),OWNER_resources_in_roles=len(resources),original_empty_clause_present=[] in support['clauses'],support_RUP_verified=True);rows.append(record);print('FINITE_BANK_UNSAT_SUPPORT',record,flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (O/'verification.json').write_text(json.dumps(dict(status='ALL3_FINITE_BANK_UNSAT_SUPPORT_SUBSETS_INDEPENDENTLY_RUP_VERIFIED',bindings=bindings,rows=rows,scope='Support subset need not be minimal. OWNER-role resources omit nodes represented through simplified negative CHOICE units; full original encoding provenance remains necessary. No general routing or ranking infeasibility, no candidate selection or promotion.'),indent=2)+'\n')
if __name__=='__main__':main()
