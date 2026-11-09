"""Reject corrupt coverage/failed witnesses; preserve original producer/auditor core."""
import ast
import copy
import json
from fractions import Fraction
from pathlib import Path
import sys
from audit_continue_primary_event_v1 import audit
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha


def main():
    old=[dict(connection_id=0,budget_integer=2),dict(connection_id=1,budget_integer=4)]
    event=dict(primary_search_connection_ids=[0,1],primary_rejected_expansions=[dict(connection_id=0,status='RETAIN_RAW_BUDGET',raw=3,physical_edge_ids=[30])],fallback={},primary_attempts=[dict(connection_id=0,physical_edge_ids=None),dict(connection_id=1,physical_edge_ids=[10])])
    qs={i:dict(connection_id=i) for i in (0,1)}
    def physical(q,path,parents):
        assert path in ([30],[10]) and not parents
        return path[0]//10
    def check(e,eligible=()):return audit(e,old,eligible,{0:Fraction(1,2),1:Fraction(1,2)},{0:0,1:1},qs,physical)
    assert check(event)
    corrupt=[]
    for field,value in [('raw',4),('raw',2),('status','UNKNOWN'),('connection_id',False),('physical_edge_ids',[10])]:
        e=copy.deepcopy(event);e['primary_rejected_expansions'][0][field]=value;corrupt.append(e)
    e=copy.deepcopy(event);e['primary_search_connection_ids']=[0];corrupt.append(e)
    e=copy.deepcopy(event);e['primary_search_connection_ids']=[1,0];corrupt.append(e)
    e=copy.deepcopy(event);e['primary_rejected_expansions']=[];corrupt.append(e)
    e=copy.deepcopy(event);e['primary_rejected_expansions']*=2;corrupt.append(e)
    e=copy.deepcopy(event);e['primary_attempts'][0]['physical_edge_ids']=[30];corrupt.append(e)
    for e in corrupt:
        try:check(e)
        except AssertionError:pass
        else:raise AssertionError('Corrupt continuation trace accepted')
    class Normalize(ast.NodeTransformer):
        def visit_ImportFrom(self,n):
            if n.module=='audit_continue_primary_event_v1':return None
            if n.module=='criticality_retained_net_continue_primary_v1':n.module='criticality_retained_net_primary_v1'
            return n
        def visit_Assign(self,n):
            for target in n.targets:
                if isinstance(target,ast.Name) and target.id=='pin_order':return None
                if isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name):
                    if target.value.id=='pin_order':return None
                    if target.value.id=='event' and isinstance(target.slice,ast.Constant) and target.slice.value=='primary_rejected_expansions':return None
            return self.generic_visit(n)
        def visit_Assert(self,n):
            if isinstance(n.test,ast.Call) and isinstance(n.test.func,ast.Name) and n.test.func.id=='audit_completion':return None
            if "p['primary_completion_policy']" in ast.unparse(n.test):return None
            return self.generic_visit(n)
        def visit_Call(self,n):
            n=self.generic_visit(n);n.keywords=[k for k in n.keywords if k.arg not in ('primary_completion_policy','complete_primary_search_after_rejection_and_isolated_witnesses_pass')];return n
    pairs=[('run_design_scoped_quotient_astar_continue_primary_v1.py','run_design_scoped_quotient_astar_retained_tree_v2.py'),('verify_scaled_present_continue_primary_full_schedule_v1.py','verify_scaled_present_retained_tree_full_schedule_v1.py')]
    for new,oldname in pairs:
        assert ast.dump(Normalize().visit(ast.parse((R/'tools'/new).read_text())),include_attributes=False)==ast.dump(ast.parse((R/'tools'/oldname).read_text()),include_attributes=False)
    contract=R/'experiments/continue_primary_contract_v1_2026-10-17/verification.json';p=json.loads(contract.read_text());assert p['all_pass'] and all(sha(k)==v for k,v in p['bindings'].items())
    sources=[Path(__file__),R/'tools/audit_continue_primary_event_v1.py',*[R/'tools'/x for pair in pairs for x in pair]]
    bindings=closure(sources);bindings[str(contract)]=sha(contract)
    out=R/'experiments/continue_primary_interface_contract_v1_2026-10-17';out.mkdir()
    (out/'verification.json').write_text(json.dumps(dict(all_pass=True,bindings=bindings,corruption_cases_rejected=len(corrupt),producer_original_core_AST_preserved_except_primary_import_protocol_and_rejection_trace=True,auditor_original_core_AST_preserved_except_extra_coverage_order_and_witness_checks=True,failed_path_cannot_be_promoted_into_fallback_attempt=True,full_XTEA_fixture_pending=True,new_neuron_model_submitted=False),indent=2)+'\n')
    print('PASS',len(corrupt),'corruptions rejected; producer and independent auditor original core AST preserved')


if __name__=='__main__':main()
