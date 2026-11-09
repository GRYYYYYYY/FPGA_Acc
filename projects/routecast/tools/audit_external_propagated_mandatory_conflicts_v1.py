"""Independent XML ownership audit after only explicit initial negative units."""
import json,hashlib,xml.etree.ElementTree as ET
from array import array
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'prospective_external_family_blocker_release_v1_2026-10-19'
C=E/'prospective_external_family_blocker_release_cnf_v1_2026-10-19'
O=E/'prospective_external_family_propagated_mandatory_audit_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 proof=C/'independent_structure_verification_v1.json';a=read(proof);assert all(sha(p)==h for p,h in a['bindings'].items());graph=next(Path(p) for p in a['bindings'] if p.endswith('/rr_graph.xml'));caps=array('I');dest=array('I');types=[];stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));types.append(e.get('type'))
  elif e.tag=='edge' and parent=='rr_edges':dest.append(int(e.get('sink_node')))
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 O.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in (proof,graph,Path(__file__).resolve())};rows=[]
 for ep in range(1,4):
  case=f'w160/episode_{ep:02d}';cp=C/case/'encoding.json';bp=B/case/'candidate_bank.jsonl';cnf=read(cp);neg={-x[0] for x in cnf['clauses'] if len(x)==1 and x[0]<0};roles={(v['key'][0],v['key'][1]):i for i,v in enumerate(cnf['variables'],1) if v['kind']=='CHOICE'};mandatory=defaultdict(list);survivors={};empty=[];original_required=defaultdict(set)
  for line in bp.read_text().splitlines():
   row=json.loads(line);net=row['net_id'];owned_options=[];remaining=[]
   for index,candidate in enumerate(row['candidates']):
    owned={r['source'] for r in candidate['records']}
    for r in candidate['records']:owned.update(dest[eid] for eid in r['answer']['physical_edge_ids'])
    owned_options.append(owned)
    if roles[net,index] not in neg:remaining.append(index)
   for node in set.intersection(*owned_options):original_required[node].add(net)
   survivors[net]=remaining
   if not remaining:empty.append(net);continue
   for node in set.intersection(*(owned_options[i] for i in remaining)):
    if caps[node]==1:mandatory[node].append(net)
  conflicts=[dict(node=node,type=types[node],NETs=sorted(nets),surviving_options={net:survivors[net] for net in sorted(nets)},originally_mandatory_NETs=sorted(original_required[node])) for node,nets in sorted(mandatory.items()) if len(nets)>1]
  # Every surviving option uses the resource; all removed options have actual negative unit clauses.
  p=O/f'episode_{ep:02d}.json';p.write_text(json.dumps(dict(case=case,initial_empty_NETs=empty,propagated_conflicts=conflicts,surviving_domain_sizes={n:len(v) for n,v in survivors.items()}),indent=2)+'\n')
  for q in (cp,bp,p):bindings[str(q)]=sha(q)
  row=dict(case=case,initial_empty_domains=len(empty),propagated_conflict_resources=len(conflicts),NETs_in_conflicts=len({n for c in conflicts for n in c['NETs']}),conflict_types={t:sum(c['type']==t for c in conflicts) for t in sorted({c['type'] for c in conflicts})});rows.append(row);print('PROPAGATED_MANDATORY_AUDIT',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='ALL3_ORIGINAL_XML_INITIAL_UNIT_SURVIVING_DOMAIN_OWNERSHIP_AUDITED',bindings=bindings,rows=rows,scope='Exactly one pruning pass by explicit original negative CHOICE units, followed by mandatory-owner intersection. Not full propagation closure, minimal core, general graph or ranking infeasibility. No candidates generated or selected, labels read or budgets changed.'),indent=2)+'\n')
if __name__=='__main__':main()
