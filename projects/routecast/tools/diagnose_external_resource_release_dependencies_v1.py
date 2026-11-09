"""Label-using two-bank warm/native release-dependency diagnosis.
Capacity1 constraints exact; all nonunit resources must be invariant and legal.
"""
import json
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from binary_capacity_dependency_v1 import analyse
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
    O=R/'experiments/prospective_external_family_release_dependencies_v1_2026-10-19';O.mkdir(exist_ok=False);s=read(D/'specifications/w160/episode_01/comparison_spec.json');graph,digest,nodes,fields,rc,qs=load_endpoints(s['endpoint']);caps=fields['capacities'];slots={eid:i for i,eid in enumerate(fields['edge_ids'])};dest=fields['dest_ranks'];rows=[];contract=R/'experiments/binary_capacity_dependency_contract_v1_2026-10-19/verification.json';bindings={str(p):sha(p) for p in [graph,Path(__file__).resolve(),R/'tools/binary_capacity_dependency_v1.py',contract]}
    for episode in (1,2,3):
        case=f'w160/episode_{episode:02d}';specfile=D/'specifications'/case/'comparison_spec.json';s=read(specfile);ep=read(s['endpoint']);assert ep['graph_sha256']==digest
        wp=D/'predictions'/case/'warm/native_retained/verification.json';wa=read(wp);assert wa['native_staged_state_independent_xml_pass'];warm=read(wp.parent/'initial.json');old={r['connection_id']:r for r in warm['records']};A=defaultdict(set)
        for r in old.values():A[r['net_id']].add(r['source']);A[r['net_id']].update(dest[slots[e]] for e in r['answer']['physical_edge_ids'])
        warm_occ=Counter(n for ns in A.values() for n in ns);assert dict(warm_occ)=={int(n):v for n,v in warm['ledger'].items()}
        route=Path(s['label_physical_audit']).parent/'output.route';native_paths,native_rows,ledger=load_complete(route,ep,nodes,fields,rc);B=defaultdict(set);native={r['connection_id']:r for r in native_rows};forbidden=set()
        for q in ep['connections']:
            cid=q['connection_id'];B[q['net_id']].update(n for n,switch in native_paths[cid])
            if native[cid]['delay_integer']>old[cid]['budget_integer']:forbidden.add(q['net_id'])
        native_occ=Counter(n for ns in B.values() for n in ns);assert dict(native_occ)==dict(ledger.occupancy) and all(v<=caps[n] for n,v in native_occ.items())
        result=analyse(dict(A),dict(B),caps,forbidden)
        # Independent concrete witness verification, without relying on SCC IDs.
        index={net:i for i,net in enumerate(result['nets'])};witness_edges=0
        if not result['satisfiable']:
            cert=result['unsat_certificate'];variable=index[cert['net_id']]
            for key,start,end in [('false_implies_true',2*variable,2*variable+1),('true_implies_false',2*variable+1,2*variable)]:
                cursor=start
                for edge in cert[key]:
                    u,v=edge['source_literal'],edge['target_literal'];assert u==cursor;r=edge['reason'];kind=r['kind']
                    if kind=='budget_forbids_B':
                        net=r['net_id'];assert net in forbidden;assert (u,v)==(2*index[net]+1,2*index[net])
                    elif kind=='two_A_owners':
                        i,j=r['NETs'];n=r['node'];assert i!=j and n in A[i]&A[j] and caps[n]==1;assert (u,v) in [(2*index[i],2*index[j]+1),(2*index[j],2*index[i]+1)]
                    else:
                        assert kind=='B_requires_A_release';i,j=r['requester'],r['owner'];n=r['node'];assert i!=j and n in B[i]&A[j] and caps[n]==1;assert (u,v) in [(2*index[i]+1,2*index[j]+1),(2*index[j],2*index[i])]
                    cursor=v;witness_edges+=1
                assert cursor==end
        else:
            counts=Counter(n for net in A for n in (B[net] if result['assignment_B'][net] else A[net]));assert all(v<=caps[n] for n,v in counts.items());assert all(not result['assignment_B'][net] for net in forbidden)
        detail=O/f'episode_{episode:02d}_dependency_proof.json';detail.write_text(json.dumps(result,indent=2)+'\n')
        row={k:result[k] for k in ['satisfiable','clauses','implication_edges','unit_resources','constant_nonunit_resources','dependency_edges','budget_forbidden_B','budget_allowed_B_blocked_by_release_dependencies','nontrivial_dependency_SCCs','unblocked_nontrivial_dependency_SCCs']};row.update(case=case,largest_dependency_SCCs=result['dependency_SCC_sizes'][:5],concrete_unsat_witness_edges_verified=witness_edges);rows.append(row)
        for p in [specfile,Path(s['endpoint']),wp,wp.parent/'initial.json',Path(s['label_proof']),route,detail]:bindings[str(p)]=sha(p)
        print('RELEASE_DEPENDENCY',json.dumps(row),flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (O/'verification.json').write_text(json.dumps(dict(status='ALL3_FIXED_WARM_NATIVE_TWO_BANK_RESOURCE_DEPENDENCIES_DIAGNOSED',bindings=bindings,rows=rows,scope='Retrospective label oracle. Exact full-node capacity plus existing perconnection-budget choice constraints only within the supplied two-bank warm/native candidates. Nonunit capacities proved invariant; unit constraints complete. UNSAT verified by concrete implication cycles, not a claim that general routing or other budget-compatible trees are impossible. No objective guard relaxation, learned score, deployed candidate or promotion.'),indent=2)+'\n')
if __name__=='__main__':main()
