"""Diagnostic-only per-NET ownership errors; labels never enter prediction."""
import json,sys,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from native_route_ledger_import_compact import physical_paths
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';D=E/'prospective_external_family_fixed_nominal_NET_error_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 decision=read(A/'research_decision_v1.json');assert all(sha(p)==h for p,h in decision['bindings'].items());D.mkdir(exist_ok=False);cases=read(A/'protocol.json')['cases'];g=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);bindings={str(g):sha(g),str(A/'research_decision_v1.json'):sha(A/'research_decision_v1.json'),str(Path(__file__).resolve()):sha(__file__)}
 (D/'protocol.json').write_text(json.dumps(dict(cases=[c['case'] for c in cases],policy='All3 and all4 forecast arms, both warm initializers and previous source. Fixed original labels, per-NET unique ownership, resource and inclusive-bin signed counts. Categories by endpoint source/sink movement only. Absolute group errors can cancel and are not additive; report additive per-NET churn separately. Diagnostic target labels never used for predictor or selecting winners.',bindings=bindings),indent=2)+'\n');us=array('I');vs=array('I');stack=[]
 for event,e in ET.iterparse(g,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')))
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 def owners(p):
  frame=read(p);out=defaultdict(set)
  for q in frame['records']:
   u=q['source'];out[q['net_id']].add(u)
   for eid in q['answer']['physical_edge_ids']:assert us[eid]==u;u=vs[eid];out[q['net_id']].add(u)
   assert u==q['sink']
  assert dict(Counter(n for ns in out.values() for n in ns))=={int(n):v for n,v in frame['ledger'].items()};bindings[str(p)]=sha(p);return out,frame
 results=[]
 for c in cases:
  case=c['case'];ep=read(Path(c['endpoint']));source,sourceframe=owners(Path(c['source_frame']));srcmeta={q['connection_id']:q for q in sourceframe['records']};categories={}
  for q in ep['connections']:
   old=srcmeta[q['connection_id']];n=q['net_id'];assert n==old['net_id'];category='source_moved' if q['source']!=old['source'] else 'sink_only' if q['sink']!=old['sink'] else 'endpoint_unchanged';rank={'endpoint_unchanged':0,'sink_only':1,'source_moved':2}
   if rank[category]>rank.get(categories.get(n),-1):categories[n]=category
  name_to_net={name:int(n) for n,name in ep['net_names'].items()};route=Path(c['label_physical_audit']).parent/'output.route';target=defaultdict(set)
  for name,paths in physical_paths(route).items():
   if not paths:continue
   net=name_to_net[name]
   for path in paths:target[net].update(node for node,switch in path)
  label=read(Path(c['label_physical_audit']));assert dict(Counter(n for ns in target.values() for n in ns))=={int(n):v for n,v in label['node_occupancy'].items()};assert set(source)==set(target)==set(categories)
  spec=read(Path(c['original_comparison_spec']));domain=Path(spec['domain_proof']).parent;resources=[json.loads(x) for x in (domain/'resources.jsonl').read_text().splitlines()];rids={x['id'] for x in resources};binmap={x['id']:[tuple(k) for k in x['bins']] for x in resources};frames={'previous_source':source}
  for init in ('raw_min','native_retained'):
   frames[init+'_warm']=owners(Path(c['warm'])/init/'initial.json')[0]
   for policy in ('warm_timing_frozen','warm_timing_round_updated'):frames[init+'/'+policy]=owners(A/case/init/policy/'sketch.json')[0]
  pernet=[]
  for n in sorted(target):
   truth=target[n]&rids;prior=source[n]&rids;pernet.append(dict(net_id=n,category=categories[n],target_changed_from_source=truth!=prior,target_added=len(truth-prior),target_removed=len(prior-truth),models={name:dict(extra=len((ns[n]&rids)-truth),missing=len(truth-(ns[n]&rids)),changed_from_source=(ns[n]&rids)!=prior) for name,ns in frames.items()}))
  out=D/case;out.mkdir(parents=True);payload=out/'per_NET.json';payload.write_text(json.dumps(pernet)+'\n');summaries={};signed={}
  for name,ns in frames.items():
   grouped={k:Counter() for k in ('endpoint_unchanged','source_moved','sink_only')};stats={k:dict(NETs=0,target_changed_NETs=0,target_churn=0,prediction_changed_NETs=0,per_NET_extra=0,per_NET_missing=0) for k in grouped}
   for row in pernet:
    n=row['net_id'];cat=row['category'];s=stats[cat];s['NETs']+=1;s['target_changed_NETs']+=row['target_changed_from_source'];s['target_churn']+=row['target_added']+row['target_removed'];s['prediction_changed_NETs']+=row['models'][name]['changed_from_source'];s['per_NET_extra']+=row['models'][name]['extra'];s['per_NET_missing']+=row['models'][name]['missing'];grouped[cat].update((ns[n]&rids)-(target[n]&rids));grouped[cat].subtract((target[n]&rids)-(ns[n]&rids))
   total=Counter()
   for cat,delta in grouped.items():
    total.update(delta);bins=Counter()
    for node,value in delta.items():
     for key in binmap[node]:bins[key]+=value
    stats[cat].update(resource_signed_L1=sum(abs(x) for x in delta.values()),inclusive_bin_signed_L1=sum(abs(x) for x in bins.values()))
   ownledger=Counter(n for support in ns.values() for n in support);truthledger=Counter(n for support in target.values() for n in support);assert all(total[n]==ownledger[n]-truthledger[n] for n in rids);bin_total=Counter()
   for node,value in total.items():
    for key in binmap[node]:bin_total[key]+=value
   summaries[name]=dict(categories=stats,resource_total_L1=sum(abs(x) for x in total.values()),inclusive_bin_total_L1=sum(abs(x) for x in bin_total.values()));signed[name]={cat:{str(n):v for n,v in delta.items() if v} for cat,delta in grouped.items()}
  signedfile=out/'signed_resource_errors.json';signedfile.write_text(json.dumps(signed)+'\n');results.append(dict(case=case,models=summaries));print(json.dumps(dict(case=case,prior=summaries['previous_source'],native_updated=summaries['native_retained/warm_timing_round_updated'])),flush=True)
  for p in [route,Path(c['label_physical_audit']),Path(c['endpoint']),domain/'resources.jsonl',domain/'spatial_bins.json',payload,signedfile]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(dict(status='ALL3_ALL7_STATES_NET_OWNERSHIP_SIGNED_RESOURCE_AND_INCLUSIVE_BIN_ERRORS_ACCOUNTED',rows=results,bindings=bindings,scope='Descriptive decomposition, not causal identification, prospective prediction or oracle acceptance. Per-NET churn additive; signed category L1 can cancel.'),indent=2)+'\n')
if __name__=='__main__':main()
