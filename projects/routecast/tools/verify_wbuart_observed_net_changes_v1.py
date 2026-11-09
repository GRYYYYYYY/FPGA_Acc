"""Independent branch-route parser cross-check of target per-NET change counts."""
import json,hashlib,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from native_route_ledger_import_compact import physical_paths
E=R/'experiments';D=E/'wbuart_observed_net_changes_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(k)==h for k,h in v['bindings'].items());workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json');graphs={};rows=[]
 for row in v['rows']:
  s=read(next(c['specification'] for c in workflow['comparisons'] if c['case']==row['case']));ep=read(s['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[(int(e.attrib['src_node']),int(e.attrib['sink_node'])) for _,e in ET.iterparse(g) if e.tag=='edge']
  edges=graphs[g];source=read(s['source_frame']);old={r['connection_id']:r for r in source['records']};src=defaultdict(set);ids={json.loads(l)['id'] for l in (Path(s['domain_proof']).parent/'resources.jsonl').read_text().splitlines()}
  for q in old.values():
   for eid in q['answer']['physical_edge_ids']:src[q['net_id']].update(edges[eid])
  names={name:int(n) for n,name in ep['net_names'].items() if int(n) in src};target={names[name]:{node for branch in branches for node,switch in branch}&ids for name,branches in physical_paths(Path(s['label_physical_audit']).parent/'output.route').items() if name in names};assert set(target)==set(src);dirty=set();moved=set()
  for q in ep['connections']:
   a=old[q['connection_id']]
   if (q['source'],q['sink'])!=(a['source'],a['sink']):dirty.add(q['net_id'])
   if q['source']!=a['source']:moved.add(q['net_id'])
  counts=Counter()
  for net in src:
   cat='source_moved' if net in moved else 'sink_only' if net in dirty else 'endpoint_unchanged';counts[cat]+=((src[net]&ids)!=target[net])
  for method,data in row['methods'].items():
   for cat,n in counts.items():assert data[cat]['observed_changed_NETs']==n
  rows.append({'case':row['case'],'observed_changed_NETs':dict(counts)})
 assert len(rows)==9
 (D/'independent_target_change_verification_v1.json').write_text(json.dumps({'status':'ALL9_OBSERVED_NET_CHANGES_CROSS_PARSER_VERIFIED','rows':rows,'scope':'Independent native branch parser verifies observed change counts across all3 methods; predicted signed overlap counts remain producer-checked only.','bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)}},indent=2)+'\n');print('ALL9_OBSERVED_NET_CHANGES_CROSS_PARSER_VERIFIED')
if __name__=='__main__':main()
