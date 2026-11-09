"""Reconstruct all whole-NET CNF roles/clauses independently from original XML."""
import json,xml.etree.ElementTree as ET
from array import array
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];B=R/'experiments/prospective_external_family_global_mask_probe_v2_2026-10-19';O=R/'experiments/prospective_external_family_global_mask_cnf_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
    root=read(O/'verification.json');ip=B/'independent_verification_v1.json';a=read(ip);assert a['status']=='ALL_DOMINANT_UNION_MASK_CANDIDATES_INDEPENDENTLY_PHYSICALLY_VERIFIED';assert all(sha(p)==h for p,h in a['bindings'].items())
    first=next(r for r in root['rows'] if r['status']=='CNF_PREPARED_NOT_SOLVED');bankproof=read(O/first['case']/'verification.json');graph=next(Path(p) for p in bankproof['bindings'] if p.endswith('/rr_graph.xml'));caps=array('I');dest=array('I');stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='node' and parent=='rr_nodes':assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')))
        elif e.tag=='edge' and parent=='rr_edges':dest.append(int(e.get('sink_node')))
        if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
        stack.pop()
    rows=[];bindings={str(p):sha(p) for p in [O/'verification.json',ip,graph,Path(__file__).resolve()]}
    for row in root['rows']:
        if row['status']=='UNAVAILABLE_SOURCE_BRANCH':continue
        case=row['case'];d=O/case;path=d/'encoding.json';cnf=read(path);roles={}
        for index,v in enumerate(cnf['variables'],1):
            key=(v['kind'],tuple(v['key']));assert key not in roles;roles[key]=index
        bank={};uses=defaultdict(lambda:defaultdict(set));expected_roles=set()
        for line in (B/case/'candidate_bank.jsonl').read_text().splitlines():
            b=json.loads(line);net=b['net_id'];assert net not in bank;choices=[]
            for i,candidate in enumerate(b['candidates']):
                role=('CHOICE',(net,i));expected_roles.add(role);x=roles[role];choices.append(x);owned={r['source'] for r in candidate['records']}
                for r in candidate['records']:owned.update(dest[eid] for eid in r['answer']['physical_edge_ids'])
                for n in owned:assert caps[n]>0;uses[n][net].add(x)
            bank[net]=choices
        clauses=set();constants=[];conflicts=[]
        def add(*lits):clauses.add(tuple(sorted(set(lits))))
        for net,xs in bank.items():
            add(*xs)
            for i,x in enumerate(xs):
                for y in xs[i+1:]:add(-x,-y)
        for n,owners in sorted(uses.items()):
            cap=caps[n]
            if cap>1:
                for net,xs in owners.items():assert xs==set(bank[net])
                constants.append(dict(node=n,capacity=cap,NETs=sorted(owners)))
                if len(owners)>cap:add()
                continue
            assert cap==1
            if len(owners)==1:continue
            forced=sorted(net for net,xs in owners.items() if xs==set(bank[net]))
            if len(forced)>=2:add();conflicts.append(dict(node=n,NETs=forced));continue
            if forced:
                for net,xs in owners.items():
                    if net!=forced[0]:
                        for x in xs:add(-x)
                continue
            auxiliary=[]
            for net,xs in sorted(owners.items()):
                role=('OWNER',(n,net));expected_roles.add(role);z=roles[role];auxiliary.append(z)
                for x in xs:add(-x,z)
                add(-z,*xs)
            for i,z in enumerate(auxiliary):
                for w in auxiliary[i+1:]:add(-z,-w)
        assert expected_roles==set(roles) and constants==cnf['constant_nonunit_resources'] and conflicts==cnf['mandatory_unit_conflicts'];assert [list(c) for c in sorted(clauses)]==cnf['clauses']
        lines=(d/'problem.cnf').read_text().splitlines();assert lines[0]==f"p cnf {len(roles)} {len(clauses)}";parsed=[list(map(int,line.split())) for line in lines[1:]];assert all(c[-1]==0 for c in parsed) and [c[:-1] for c in parsed]==cnf['clauses']
        for q in [path,d/'problem.cnf',B/case/'candidate_bank.jsonl',d/'verification.json']:bindings[str(q)]=sha(q)
        rows.append(dict(case=case,variables=len(roles),clauses=len(clauses),constant_nonunit_resources=len(constants),all_roles_clauses_and_DIMACS_exact=True));print('CNF_STRUCTURE_PASS',case,len(roles),len(clauses),flush=True)
    assert len(rows)==3 and all(sha(p)==h for p,h in bindings.items())
    (O/'independent_structure_verification_v1.json').write_text(json.dumps(dict(status='ALL3_COMPLETE_NET_BANK_CNFS_INDEPENDENT_XML_ROLES_AND_CLAUSES_VERIFIED',bindings=bindings,rows=rows,scope='Exact finite-bank logical projection, including invariant nonunit owners. Not a solver result, original routing infeasibility or forecast gain.'),indent=2)+'\n')
if __name__=='__main__':main()
