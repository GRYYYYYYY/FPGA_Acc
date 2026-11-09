"""Read-only localization of retained fixed-budget capacity failures."""
from pathlib import Path
import csv,struct,json,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work';O=W/'additional_parent_failure_localization_20261021'
def main():
 O.mkdir(exist_ok=False);refs={};rows=[]
 def read(p):
  data=p.read_bytes();refs[str(p)]=hashlib.sha256(data).hexdigest();return data
 for label in ['seq_seed1','seq_seed2']:
  audit=json.loads(read(W/'additional_circuit_parent_capacity_failure_review_20261021'/f'{label}.json'))
  root=W/'additional_circuit_full_graph_roundtrip_20261020/cases'/label
  dies=read(root/'topology.node_die');boxes=read(root/'topology.node_box')
  die=lambda n:struct.unpack_from('<H',dies,n*2)[0]
  violations={v['node']:dict(v,layer=die(v['node']),xy_box=struct.unpack_from('<HHHH',boxes,v['node']*8),incoming_uses=[]) for v in audit['violations']}
  tree=W/'additional_circuit_frozen_parents_20261020/parents'/label/'route.route_trees.csv'
  for row in csv.DictReader(read(tree).decode().splitlines()):
   child=int(row['child']);parent=int(row['parent'])
   if child in violations:violations[child]['incoming_uses'].append(dict(net=int(row['net_id']),parent=parent,parent_layer=die(parent),cross_layer=die(parent)!=die(child)))
  for v in violations.values():assert sorted(x['net'] for x in v['incoming_uses'])==v['nets']
  rows.append(dict(label=label,violations=list(violations.values()),overused_resources=audit['overused_resources']))
 read(Path(__file__).resolve())
 report=dict(status='retained_capacity_failures_localized_without_reroute',rows=rows,source_sha256=refs,scope='Coordinates and explicit VPR layers of the already independently reconstructed overused destination resources and their incoming tree edges. No optimality, root cause, physical SLL, quality repair or budget extension claim.',research_complete=False)
 (O/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
