"""Independent success topology and actual per-width demand, not canonical pin closure."""
import json,sys,re
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
D=R/'experiments/sha1_native_width_cohort_v1_2026-10-10';rp=D/'receipt.json';r=json.loads(rp.read_text());row=next(x for x in r['rows'] if x['width']==96);assert row['exit_code']==0
bindings={**r['bindings'],**row['files'],str(rp):sha(rp),**closure([Path(__file__)])};assert all(sha(k)==v for k,v in bindings.items())
F=R/'experiments/sha1_width_native_demand_v1_2026-10-10/96';proof=F/'verification.json';v=json.loads(proof.read_text());assert v['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'];assert all(sha(k)==h for k,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(proof)]=sha(proof)
epf=F/'endpoints.json';ep=json.loads(epf.read_text());graph=D/'96/rr_graph.xml';assert sha(graph)==ep['graph_sha256'];bindings[str(epf)]=sha(epf)
route=D/'96/output.route';a=audit(graph,route);names={int(m[1]):m[2] for line in route.read_text().splitlines() if (m:=NET.match(line))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);nameset=set(ep['net_names'].values());observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in nameset);assert observed==required and a['overflow_units']==0
text=(D/'96/native.log').read_text();assert 'Completed routing consistency check successfully.' in text and 'VPR succeeded' in text;iterations=int(re.search(r'Successfully routed after (\d+) routing iterations',text)[1]);assert iterations==19
ap=D/'96/physical_audit_v1.json';ap.write_text(json.dumps(a)+'\n');bindings[str(ap)]=sha(ap);assert all(sha(k)==h for k,h in bindings.items())
(D/'96/physical_verification_v1.json').write_text(json.dumps(dict(bindings=bindings,all_original_XML_physical_queries_branch_arcs_and_capacity_pass=True,physical_connections=sum(observed.values()),overflow_units=0,iterations=iterations,canonical_reload_pass=False,scope='Native96 FULL and independent physical route audit, actual96 demand graph. Canonical ignored-pin reload pending, no HDL/timing/strict-heldout/infeasibility or model failure-classification proof.'),indent=2)+'\n');print('PASS width96 physical',sum(observed.values()),iterations)
