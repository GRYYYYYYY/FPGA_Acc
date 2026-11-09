"""Independent fixed-point closure and full-ledger group replacement rebuild."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_donor_closure_diagnosis_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());graphs={};rows=[]
 for c in v['rows']:
  ep=read(c['endpoint']);graph=ep['inputs']['graph']['path']
  if graph not in graphs:
   caps=[];ends=[]
   for _,e in ET.iterparse(graph):
    if e.tag=='node' and e.get('capacity') is not None:caps.append(int(e.attrib['capacity']))
    if e.tag=='edge':ends.append(int(e.attrib['sink_node']))
   graphs[graph]=caps,ends
  caps,ends=graphs[graph];old=defaultdict(set);target=defaultdict(set);refs={r['net_id']:r for r in read(c['native_reference_payload'])}
  for r in read(c['warm_frame'])['records']:old[r['net_id']].add(r['source']);old[r['net_id']].update(ends[e] for e in r['answer']['physical_edge_ids'])
  for net,ref in refs.items():
   for r in ref['native_records']:target[net].add(r['source']);target[net].update(ends[e] for e in r['answer']['physical_edge_ids'])
  inverse=defaultdict(set)
  for net,nodes in old.items():
   for node in nodes:inverse[node].add(net)
  data=read(c['payload']);deps={}
  for net in old:
   dependencies=set()
   for node in target[net]:
    if node not in old[net]:dependencies.update(inverse[node])
   dependencies.discard(net);deps[net]=dependencies
  assert {str(n):sorted(ns) for n,ns in deps.items()}==data['dependency_adjacency'];groups={g['group_id']:g for g in data['groups']};initial=Counter(n for ns in old.values() for n in ns);over=lambda ledger:sum(max(0,count-caps[n]) for n,count in ledger.items());initial_over=over(initial);assert initial_over==c['initial_overflow_units']
  for g in groups.values():
   chosen=set(g['NETs']);rebuilt=Counter(n for net in old for n in (target[net] if net in chosen else old[net]));actual=over(rebuilt);assert actual-initial_over==g['joint_overflow_delta']<=0 and actual==g['resulting_overflow_units'];assert g['budget_incompatible_NETs']==sorted(n for n in chosen if refs[n]['budget_violating_CIDs']);assert g['all_target_paths_budget_compatible']==all(not refs[n]['budget_violating_CIDs'] for n in chosen)
  for r in data['roots']:
   closure={r['root_NET']}
   while True:
    updated=closure|{d for n in closure for d in deps[n]}
    if updated==closure:break
    closure=updated
   assert closure==set(groups[r['group_id']]['NETs']);assert refs[r['root_NET']]['overflow_delta']==r['root_single_overflow_delta']>0
  assert len(data['roots'])==sum(q['overflow_delta']>0 for q in refs.values());rows.append({'case':c['case'],'roots':len(data['roots']),'unique_groups':len(groups),'all_fixed_points_and_full_ledger_rebuilds_pass':True})
 assert len(rows)==9
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL9_DONOR_FIXED_POINTS_AND_JOINT_FULL_LEDGER_REBUILDS_VERIFIED','rows':rows,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Independent fixed-point traversal and full uniqueNET occupancy rebuild, same authenticated source/target records and graph semantics. Conservative closure not minimum; joint objective not evaluated, no deployable reference-guided grouping.'},indent=2)+'\n');print('ALL9_DONOR_FIXED_POINTS_AND_JOINT_FULL_LEDGER_REBUILDS_VERIFIED')
if __name__=='__main__':main()
