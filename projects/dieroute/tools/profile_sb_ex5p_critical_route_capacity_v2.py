"""Check exact baseline-path capacity with all other final nets fixed; no rerouting."""
import collections,csv,hashlib,json,struct,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb_ex5p_critical_route_capacity_v2_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def sha(f):
  p=Path(f);key=str(p)
  if key not in refs:
   h=hashlib.sha256()
   with p.open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 f=R/'work/sb_ex5p_critical_arc_RR_binding_v5_20261015/independent_audit.json';binding=json.loads(f.read_text())
 for file,h in binding['source_sha256'].items():assert sha(file)==h,file
 baseline=next(v for v in binding['outcomes'] if v['case']=='baseline');base_nodes=baseline['path'];models={v['case']:v for v in binding['outcomes']};a=R/'work/sb_ex5p_native_STA_path_alignment_20261015';protocol=json.loads((a/'protocol.json').read_text());precision=R/'work/rr_remaining_tail_precision_development_v2_20261015/protocol.json';config=json.loads(precision.read_text());case=next(v for v in config['cases'] if v['label']=='ex5p');initial_path=Path(case['input_prefix']+'.resources');assert sha(initial_path)==config['source_sha256'][str(initial_path)];initial=list(struct.iter_unpack('<HHHHII',initial_path.read_bytes()));assert len(initial)==336312 and all(v[0]==0 for v in initial)
 rr=Path(case['native_case'])/'rr_graph.xml';caps={}
 for _,el in E.iterparse(rr,events=['end']):
  if el.tag=='node':
   node=int(el.get('id'))
   if node in base_nodes:caps[node]=int(el.get('capacity'));assert caps[node]==initial[node][1]
   el.clear()
   if len(caps)==len(base_nodes):break
 assert len(caps)==len(base_nodes)
 net_names={int(row['net_id']):row['net'] for row in csv.DictReader((R/'work/sb_native_roundtrip_preflight_20261015/layers3_cw80/connections.csv').open())};results=[]
 for row in protocol['cases']:
  label=row['label']
  if label=='baseline':continue
  directory=Path(row['route']).parent.parent;trees=directory/'route.route_trees.csv';resource_path=directory/'route.resources';net_nodes=collections.defaultdict(set)
  for item in csv.DictReader(trees.open()):
   net=int(item['net_id']);net_nodes[net].update(int(item[k]) for k in ['source','parent','child'])
  owners=collections.defaultdict(set)
  for net,ns in net_nodes.items():
   for node in ns:assert 0<=node<len(initial);owners[node].add(net)
  resources=list(struct.iter_unpack('<HHHHII',resource_path.read_bytes()));assert len(resources)==len(initial)
  for node,(old,new) in enumerate(zip(initial,resources)):assert new[1]==old[1] and new[0]==len(owners.get(node,())) and new[0]<=new[1],(label,node,new[:2],owners.get(node))
  observations=[]
  for node in base_nodes:
   occ,cap=resources[node][:2];self_owned=node in net_nodes[138];others=sorted(owners.get(node,set())-{138});increment=0 if self_owned else 1
   observations.append(dict(node=node,RR_type=binding['RR_nodes'][str(node)]['type'],layer=binding['RR_nodes'][str(node)]['loc']['layer'],occupancy=occ,capacity=cap,already_owned_by138=self_owned,additional_occupancy=increment,capacity_blocked=occ+increment>cap,other_owner_nets=[dict(id=n,name=net_names[n]) for n in others]))
  blocked=[v for v in observations if v['capacity_blocked']]
  assert all(not v['already_owned_by138'] and len(v['other_owner_nets'])>=v['capacity'] for v in blocked)
  results.append(dict(case=label,all_resource_occupancies_rebuilt=336312,nets_rebuilt=len(net_nodes),baseline_path_nodes=len(base_nodes),blocked_baseline_nodes=len(blocked),blocked_nodes=blocked,baseline_path_capacity_feasible_with_other_nets_fixed=not blocked,observations=observations))
  sha(trees);sha(resource_path)
 for file in [f,a/'protocol.json',precision,initial_path,rr,R/'work/sb_native_roundtrip_preflight_20261015/layers3_cw80/connections.csv',Path(__file__).resolve()]:sha(file)
 report=dict(status='baseline_task895_exact_RR_path_capacity_checked_with_other_final_nets_fixed',outcomes=results,source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Both final candidates independently reconstruct all336312 resource occupancies from per-net unique RR tree nodes; capacities equal immutable input, selected baseline capacities match RR XML. Test only adding exact baseline task895 node set to net138 with every other net fixed. A blocked absent-from-self node proves exact path cannot be reused by net138 alone; no blocked nodes would not prove tree/edge compatibility, timing or joint quality. No rerouting, alternative-path impossibility, selection or physical result.')
 with (P/'independent_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(json.dumps([dict(case=v['case'],nets=v['nets_rebuilt'],blocked_baseline_nodes=v['blocked_baseline_nodes'],blocked_nodes=v['blocked_nodes']) for v in results]))
if __name__=='__main__':main()
