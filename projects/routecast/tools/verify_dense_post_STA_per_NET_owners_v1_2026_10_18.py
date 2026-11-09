"""Per-NET parent/ownership reconciliation with independently XML-certified source paths."""
import array,collections,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_dense_post_STA_source_v1_2026-10-18';bindings=closure([Path(__file__)])
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p):
  d=load(p);assert all(sha(k)==h for k,h in d['bindings'].items());bindings.update(d['bindings']);return d
 dense=admit(root/'verification_v1.json');assert dense['all_physical_pin_global_NET_local_identity_and_RR_endpoints_equal'];sourceproof=admit(E/'mmc_native_source_checkpoint_v1_2026-10-18/independent_xml_verification_v1.json');assert sourceproof['all_native_paths_exact'];source=load(E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json');pins={r['connection_id']:r for r in load(root/'dense_physical_criticalities.json')};geo=admit(E/'mmc_endpoint_geometry_topology_v2_2026-10-18/receipt.json');admit(E/'mmc_endpoint_geometry_topology_v2_2026-10-18/independent_verification_v1.json');idxpath=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';assert geo['bindings'][str(idxpath)]==sha(idxpath);idx=load(idxpath);assert sys.byteorder==idx['byteorder'];arrays={}
 for key in ['edge_source','edge_destination']:
  d=idx['arrays'][key];assert sha(d['path'])==d['sha256']==geo['bindings'][d['path']];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());assert len(a)==d['values'];arrays[key]=a;bindings[d['path']]=d['sha256']
 mapping={};expected={};owners=collections.defaultdict(set)
 for rec in source['records']:
  p=pins[rec['connection_id']];native=p['native_NET'];logical=rec['net_id'];assert mapping.setdefault(native,logical)==logical;node=rec['source'];key=(logical,node);assert expected.setdefault(key,-1)==-1;owners[logical].add(node)
  for edge in rec['answer']['physical_edge_ids']:
   assert arrays['edge_source'][edge]==node;dest=arrays['edge_destination'][edge];key=(logical,dest);assert expected.setdefault(key,node)==node;owners[logical].add(dest);node=dest
  assert node==rec['sink']
 actual={}
 with (root/'context.tsv').open() as f:
  for line in f:
   x=line.split()
   if x[0]=='T':
    net,node,parent=map(int,x[1:4]);key=(mapping[net],node);assert key not in actual;actual[key]=parent
 assert actual==expected and len(mapping)==len(owners)==55300;ledger=collections.Counter(n for nodes in owners.values() for n in nodes);assert dict(ledger)=={int(n):v for n,v in source['ledger'].items()};assert all(sha(k)==h for k,h in bindings.items())
 result=dict(status='all55300_dense_native_NET_owner_sets_and_parent_RR_relations_equal_audited_final_source_paths',bindings=bindings,NETs=len(owners),NET_node_pairs=len(actual),physical_connections=len(pins),scope='Each native NET joined through every physical CID and packed pin to source logical NET; every dense tree node and parent equals originalXML-certified final source paths. Global ledger also rebuilt. No stale criticality substitution or forecast improvement claim.')
 with (root/'per_NET_owner_verification_v1.json').open('x') as f:json.dump(result,f,indent=2)
 print('DENSE_PER_NET_OWNERS_PASS',len(owners),len(actual),flush=True)
if __name__=='__main__':main()
