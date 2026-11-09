"""Diagnose failed native artifacts; never admits an illegal source checkpoint."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET,NODE
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_executable_development_v1_2026-10-19'
def main():
    manifest=D/'native_manifest.json';m=json.loads(manifest.read_text());rows=[];bindings={str(manifest):sha(manifest),str(Path(__file__).resolve()):sha(__file__)}
    for job in m['cases']:
        if job['frame']!='source':continue
        folder=Path(job['output']);proof=folder/'verification.json';v=json.loads(proof.read_text());assert v['exit_status']==2
        assert all(sha(p)==h for p,h in v['bindings'].items());bindings[str(proof)]=sha(proof)
        graph=Path(job['command'][job['command'].index('--read_rr_graph')+1]);route=folder/'output.route';ep=json.loads(Path(job['endpoint']).read_text());row=dict(width=job['width'],source_eligible=False)
        try:
            physical=audit(graph,route);caps={};details={};stack=[]
            for event,e in ET.iterparse(graph,events=('start','end')):
                if event=='start':stack.append(e);continue
                if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
                    n=int(e.get('id'));cap=int(e.get('capacity'));occ=physical['node_occupancy'].get(str(n),0)
                    if occ>cap:details[n]=dict(node=n,type=e.get('type'),capacity=cap,occupancy=occ,location=dict(e.find('loc').attrib))
                    stack[-2].remove(e);e.clear()
                if e.tag=='rr_nodes':break
                stack.pop()
            names={};owners=defaultdict(set);net=None
            for line in route.read_text().splitlines():
                match=NET.match(line)
                if match:net=int(match[1]);names[net]=match[2]
                node=NODE.match(line)
                if node and int(node[1]) in details:owners[int(node[1])].add(net)
            actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections'])
            expected=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections'])
            row.update(original_XML_arc_branch_checks_pass=True,endpoint_multiset_complete=actual==expected,connections=len(physical['connections']),overflow_nodes=len(details),overflow_units=physical['overflow_units'],overused_node_types=dict(Counter(x['type'] for x in details.values())))
            if len(details)<=20:row['overused_nodes']=[dict(x,owner_native_NETs=sorted(owners[n])) for n,x in details.items()]
            for p in [graph,route,Path(job['endpoint'])]:bindings[str(p)]=sha(p)
        except Exception as e:row['audit_error']=repr(e)
        rows.append(row);print('FAILED_SOURCE_AUDIT',row['width'],row.get('overflow_nodes'),row.get('overused_node_types'),flush=True)
    (D/'failed_source_physical_audit_v1.json').write_text(json.dumps(dict(status='FAILED_NATIVE_ARTIFACT_DIAGNOSTICS_ONLY',bindings=bindings,rows=rows,source_eligible=False,scope='Independent original XML physical arc/branch and unique-NET occupancy checks of failed printed routes. Full endpoint coverage and small congestion do not imply legal routing, native FULL acceptance, irreducible infeasibility or a usable source checkpoint.'),indent=2)+'\n')
if __name__=='__main__':main()
