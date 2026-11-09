"""All snapshot branches, exact demand endpoints and printed congestion reconciliation."""
import json,re,sys,xml.etree.ElementTree as E
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
from source_binding_v2 import closure
D=R/'experiments/sha1_cold_iteration_routes_v1_2026-10-10';rp=D/'receipt.json';r=json.loads(rp.read_text());assert r['exit_code']==0
bindings={**closure([Path(__file__)]),str(rp):sha(rp)}
for section in ['bindings','files']:
 for k,h in r[section].items():assert sha(k)==h;bindings[k]=h
epf=R/'experiments/sha1_actual_old_linear_expat_workflow_v1_2026-10-10/cold/demand/sha1/endpoints.json';ep=json.loads(epf.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings.update({str(epf):sha(epf),str(graph):sha(graph)})
required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);nameset=set(ep['net_names'].values())
capacity={};types={};stack=[]
for ev,el in E.iterparse(graph,events=('start','end')):
 if ev=='start':stack.append(el);continue
 if el.tag=='node':
  n=int(el.get('id'));assert n not in capacity;capacity[n]=int(el.get('capacity'));types[n]=el.get('type')
 if el.tag in {'node','edge'}:
  if len(stack)>1:stack[-2].remove(el)
  el.clear()
 stack.pop()
text=(D/'native.log').read_text();start=text.index('Iter   Time');end=text.index('Restoring best routing',start);logged={}
for line in text[start:end].splitlines():
 m=re.match(r'^\s*(\d+)\s+[\d.]+\s+[\d.]+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)\s+\(',line)
 if m:logged[int(m[1])]=int(m[2])
assert sorted(logged)==list(range(1,len(r['snapshots'])+1));rows=[];out=D/'snapshot_audits_v2';out.mkdir()
for path in r['snapshots']:
 p=Path(path);i=int(p.stem.split('_')[1]);a=audit(graph,p)
 names={int(m[1]):m[2] for line in p.read_text().splitlines() if (m:=NET.match(line))}
 observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in nameset);assert observed==required
 # Independent complete perNET union reconstruction, including branches.
 from audit_native_route import NODE
 unions={};net=None
 for line in p.read_text().splitlines():
  if m:=NET.match(line):net=int(m[1]);assert net not in unions;unions[net]=set()
  elif m:=NODE.match(line):assert net is not None;unions[net].add(int(m[1]))
 occ=Counter(n for nodes in unions.values() for n in nodes)
 assert dict(occ)=={int(n):v for n,v in a['node_occupancy'].items()}
 overused={n for n,v in occ.items() if v>capacity[n]};assert len(overused)==logged[i],(i,len(overused),logged[i])
 assert a['overflow_units']==sum(max(0,v-capacity[n]) for n,v in occ.items())
 ap=out/f'iteration_{i:03d}.json';ap.write_text(json.dumps(a)+'\n');bindings[str(ap)]=sha(ap)
 rows.append(dict(iteration=i,physical_connections=sum(observed.values()),overused_rr_nodes=len(overused),overused_channel_nodes=sum(types[n] in {'CHANX','CHANY'} for n in overused),overflow_units=a['overflow_units'],full_branch_arcs_types_and_endpoints_pass=True,independent_union_and_printed_count_pass=True))
 (out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS iteration',i,len(overused),flush=True)
assert rows[-1]['overused_rr_nodes']==0 and all(sha(k)==h for k,h in bindings.items())
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_18_snapshot_physical_queries_branch_XML_union_and_log_counts_pass=True,scope='Complete printed branch/XML and physical demand audit; early snapshots explicitly permit measured overflow. Not FULL legality of congested snapshots, ignored-pin canonical closure, failure labels, heldout or timing proof.'),indent=2)+'\n')
