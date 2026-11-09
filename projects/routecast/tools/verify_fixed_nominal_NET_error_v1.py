"""Alternate XML sparse-edge parse and route-node unions for all21 states."""
import json,hashlib,xml.etree.ElementTree as ET,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from audit_native_route import NET,NODE
E=R/'experiments';D=E/'prospective_external_family_fixed_nominal_NET_error_v1_2026-10-19';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 diagnosis=read(D/'diagnosis.json');assert all(sha(p)==h for p,h in diagnosis['bindings'].items());cases=read(A/'protocol.json')['cases'];needed=set();frames={};specs={};bindings={str(D/'diagnosis.json'):sha(D/'diagnosis.json'),str(Path(__file__).resolve()):sha(__file__)}
 for c in cases:
  case=c['case'];specs[case]=c;files={'previous_source':Path(c['source_frame'])}
  for init in ('raw_min','native_retained'):
   files[init+'_warm']=Path(c['warm'])/init/'initial.json'
   for policy in ('warm_timing_frozen','warm_timing_round_updated'):files[init+'/'+policy]=A/case/init/policy/'sketch.json'
  for name,p in files.items():
   frame=read(p);frames[case,name]=frame
   for q in frame['records']:needed.update(q['answer']['physical_edge_ids'])
 graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);edges={};index=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='edge' and parent=='rr_edges':
   if index in needed:edges[index]=int(e.get('src_node')),int(e.get('sink_node'))
   index+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert set(edges)==needed;rows=[]
 for result in diagnosis['rows']:
  case=result['case'];c=specs[case];ep=read(Path(c['endpoint']));netnames={name:int(n) for n,name in ep['net_names'].items()};target=defaultdict(set);name=None
  for line in (Path(c['label_physical_audit']).parent/'output.route').read_text().splitlines():
   m=NET.match(line)
   if m:name=m[2]
   node=NODE.match(line)
   if node:target[netnames[name]].add(int(node[1]))
  spec=read(Path(c['original_comparison_spec']));resourcefile=Path(spec['domain_proof']).parent/'resources.jsonl';resources={q['id']:q for q in [json.loads(x) for x in resourcefile.read_text().splitlines()]};rids=set(resources);stored={q['net_id']:q for q in read(D/case/'per_NET.json')};signed=read(D/case/'signed_resource_errors.json');source={q['connection_id']:q for q in frames[case,'previous_source']['records']};categories={};rank={'endpoint_unchanged':0,'sink_only':1,'source_moved':2}
  for q in ep['connections']:
   n=q['net_id'];old=source[q['connection_id']];cat='source_moved' if old['source']!=q['source'] else 'sink_only' if old['sink']!=q['sink'] else 'endpoint_unchanged'
   if rank[cat]>rank.get(categories.get(n),-1):categories[n]=cat
  for name,summary in result['models'].items():
   frame=frames[case,name];support=defaultdict(set)
   for q in frame['records']:
    u=q['source'];support[q['net_id']].add(u)
    for eid in q['answer']['physical_edge_ids']:a,b=edges[eid];assert a==u;support[q['net_id']].add(b);u=b
    assert u==q['sink']
   assert dict(Counter(n for ns in support.values() for n in ns))=={int(n):v for n,v in frame['ledger'].items()};assert set(support)==set(target)==set(stored)
   deltas={cat:Counter() for cat in rank};extras=Counter();missing=Counter()
   for n in support:
    assert stored[n]['category']==categories[n];extra=(support[n]&rids)-(target[n]&rids);miss=(target[n]&rids)-(support[n]&rids);obs=stored[n]['models'][name];assert (len(extra),len(miss))==(obs['extra'],obs['missing']);cat=categories[n];extras[cat]+=len(extra);missing[cat]+=len(miss);deltas[cat].update(extra);deltas[cat].subtract(miss)
   total=Counter();totalbins=Counter()
   for cat,delta in deltas.items():
    assert {str(n):v for n,v in delta.items() if v}==signed[name][cat];s=summary['categories'][cat];assert (s['per_NET_extra'],s['per_NET_missing'])==(extras[cat],missing[cat]);assert s['resource_signed_L1']==sum(abs(v) for v in delta.values());bins=Counter()
    for n,v in delta.items():
     for k in resources[n]['bins']:bins[tuple(k)]+=v
    assert s['inclusive_bin_signed_L1']==sum(abs(v) for v in bins.values());total.update(delta);totalbins.update(bins)
   assert summary['resource_total_L1']==sum(abs(v) for v in total.values()) and summary['inclusive_bin_total_L1']==sum(abs(v) for v in totalbins.values())
  rows.append(dict(case=case,models=7,NETs=len(stored),independent_node_union_and_signed_resource_bin_errors_equal=True));print(rows[-1],flush=True)
 assert all(sha(p)==h for p,h in diagnosis['bindings'].items());(D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL21_STATE_ORIGINAL_XML_AND_DIRECT_ROUTE_NODE_UNIONS_AND_SIGNED_ERROR_DECOMPOSITIONS_PASS',rows=rows,bindings=bindings,scope='Independent alternate physical extraction, descriptive errors only. No causal or forecasting acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
