"""Original XML/Fraction counterexamples to retained-path universal minima."""
import json
from pathlib import Path
from fractions import Fraction as F
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read, arc_delay
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07'
out=ROOT/'experiments/mux_released_retained_floor_diagnosis_2026-10-07'
out.mkdir(exist_ok=True)
p=json.loads((base/'protocol.json').read_text()); rows=[]; files={}
for i in (0,2,3):
 case=next(c for c in p['cases'] if (c['width'],c['index'])==(8,i))
 file=base/f'w8_m{i}/result.json'; d=json.loads(file.read_text())
 proof=file.parent/'physical_budget_verification.json'
 assert json.loads(proof.read_text())['result_sha256']==sha(file)
 ep=json.loads(Path(case['target']).read_text()); graph=ep['inputs']['graph']['path']
 xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)
 seed=ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w8_m{i}.json'
 seed_data=json.loads(seed.read_text()); attempt=d['attempts'][-1]
 allocation=d['allocations'][attempt['allocation_index']]
 candidate=attempt['update']['repair'] or attempt['update']['incremental']
 assert candidate['completed_connections']==candidate['required_connections']
 hits=[]
 for r in candidate['records']:
  cid=r['connection_id']; actual=F(r['answer']['delay']*10**9,candidate['scale']); floor=F(allocation['floor_ns'][str(cid)])
  if actual>=floor:continue
  assert cid not in allocation['expanded'] and cid not in seed_data['expanded_connection_ids']
  assert floor==F(seed_data['floor_ns'][str(cid)])
  node=r['source'];seen={node};res,cap=classes[ids[node]];delay=res*cap/2
  for eid in r['answer']['physical_edge_ids']:
   e=xml.graph.edges[eid];assert e.source==node and e.sink not in seen
   node=e.sink;seen.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
  assert node==r['sink'] and delay*10**9==actual
  releases=[n for n,e in enumerate(candidate['events']) if e['type']=='RELEASE' and cid in e['removed_connection_ids'] and r['net_id'] in e['blocker_NETs']]
  commits=[n for n,e in enumerate(candidate['events']) if e['type']=='QUERY' and e['query']['connection_id']==cid and e['committed'] and e['answer']==r['answer']]
  assert releases and commits and max(commits)>min(releases)
  assert actual<=F(allocation['budgets_ns'][str(cid)])
  hits.append(dict(connection_id=cid,net_id=r['net_id'],actual_delay_ns=str(actual),planning_floor_ns=str(floor),release_event_indices=releases,final_commit_event_indices=commits,physical_edge_ids=r['answer']['physical_edge_ids']))
 rows.append(dict(width=8,index=i,counterexamples=hits))
 for f in (file,proof,seed,Path(case['target'])):files[str(f)]=sha(f)
assert [len(r['counterexamples']) for r in rows]==[0,0,3]
receipt=dict(source_sha256=sha(Path(__file__)),protocol_sha256=sha(base/'protocol.json'),files=files,rows=rows,scope='Original XML/Fraction path delay reconstruction; seed-floor equality and explicit released-owner/recommitted-query provenance. Existing bound physical proof covers whole-candidate capacity. Three local counterexamples disprove universal retained-path delay minima after repair, not full-CPD false rejection, global infeasibility or end-to-end gain. No producer rerun or policy change.')
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Verified three below-planning-floor paths on released NET45; complete-case counts 0/0/3',flush=True)
