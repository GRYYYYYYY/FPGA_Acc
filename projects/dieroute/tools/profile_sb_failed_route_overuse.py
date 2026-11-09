"""Profile actual failed-route overuse against native RR identity and cost sidecars."""
import argparse,collections,csv,hashlib,json,struct,xml.etree.ElementTree as ET
from pathlib import Path

def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser(description=__doc__)
 for name in ['route_prefix','topology_prefix','rr_graph','node_base_cost','output']:a.add_argument(name,type=Path)
 args=a.parse_args();prefix=args.route_prefix.resolve();top=args.topology_prefix.resolve();files=[Path(str(prefix)+s) for s in ['.json','.resources','.route_trees.csv']]+[Path(str(top)+'.node_die'),args.rr_graph.resolve(),args.node_base_cost.resolve(),Path(__file__).resolve()]
 route=json.loads(files[0].read_text());assert not route['legal']
 resources=list(struct.iter_unpack('<HHHHII',files[1].read_bytes()));owners=[r[0] for r in struct.iter_unpack('<H',files[3].read_bytes())];costs=[r[0] for r in struct.iter_unpack('<H',files[5].read_bytes())];assert len(resources)==len(owners)==len(costs)
 over={i:v for i,v in enumerate(resources) if v[0]>v[1]};assert len(over)==route['overused_resources'] and over
 users=collections.defaultdict(set);ingress=collections.Counter()
 with files[2].open() as stream:
  for r in csv.DictReader(stream):
   n,a,b=(int(r[k]) for k in ['net_id','parent','child'])
   if b in over:users[b].add(n);ingress[f'{owners[a]}->{owners[b]}']+=1
 metadata={}
 for _,e in ET.iterparse(files[4],events=['end']):
  if e.tag=='node':
   i=int(e.attrib['id'])
   if i in over:
    loc=e.find('loc');assert int(loc.attrib['layer'])==owners[i] and int(e.attrib['capacity'])==over[i][1];metadata[i]=dict(type=e.attrib['type'],loc=dict(loc.attrib))
   e.clear()
  elif e.tag=='edge':e.clear()
 assert set(metadata)==set(over)
 rows=[]
 for n,r in over.items():
  assert len(users[n])==r[0]
  rows.append(dict(node=n,layer=owners[n],native=metadata[n],occupancy=r[0],capacity=r[1],version=r[4],native_base_cost_q=costs[n],nets=sorted(users[n])))
 report=dict(status='failed_route_overuse_native_identity_layers_costs_and_net_memberships_profiled',iterations=route['iterations'],cpu_legal=False,overused_resources=len(over),type_counts=dict(collections.Counter(r['native']['type'] for r in rows)),layer_counts=dict(collections.Counter(r['layer'] for r in rows)),native_base_cost_counts=dict(collections.Counter(r['native_base_cost_q'] for r in rows)),distinct_contending_nets=len(set().union(*users.values())),incoming_tree_edge_layer_pairs=dict(ingress),rows=rows,source_sha256={str(q):sha(q) for q in files},scope='Diagnosticoneactualfailedroute;nativeidentity/capacity/layerandnet-deduplicatedoccupancycheckedforoverusednodes. NotlegalQoR,causalproof,alliterationlineageorphysicalSLLclaim.',board_result=False,research_complete=False)
 with args.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256']}))
if __name__=='__main__':main()
