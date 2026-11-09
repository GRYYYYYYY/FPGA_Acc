"""Independent core rejection, member irreducibility and full DFS leaf coverage."""
import json
from collections import defaultdict,Counter
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'adder_online_direct_conflict_cores_v1_2026-10-09';D=E/'adder_online_direct_conflict_cores_verification_v1_2026-10-09';D.mkdir(exist_ok=False);rp=S/'verification.json';r=json.loads(rp.read_text());bindings={**r['bindings'],str(rp):sha(rp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());cp=S/'cores.json';data=json.loads(cp.read_text());B=E/'adder_online_direct_joint_net_search_v5_2026-10-09';T=E/'adder_online_direct_joint_net_components_v5_2026-10-09';bank={int(c):opts for c,opts in json.loads((B/'step_3.json').read_text())['bank'].items()};decomp=json.loads((T/'decomposition.json').read_text());domains={int(c):v for c,v in decomp['domains'].items()};ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());queries={x['connection_id']:x for x in meta['connections']};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);prop=(E/'adder_online_direct_joint_net_propagation_verification_v5_2026-10-09/verification.json');proof_report=json.loads(prop.read_text());assert all(sha(p)==h for p,h in proof_report['bindings'].items());bindings.update(proof_report['bindings']);bindings[str(prop)]=sha(prop)
def legal(cid,index,selected):
 occupancy=defaultdict(set);parent={};net=queries[cid]['net_id']
 for c,i in selected.items():
  othernet=queries[c]['net_id'];path=bank[c][i]['path']
  for n,s in path:occupancy[n].add(othernet)
  if othernet==net:
   for (u,_),(n,s) in zip(path,path[1:]):assert n not in parent or parent[n]==(u,s);parent[n]=(u,s)
 path=bank[cid][index]['path']
 return all(len(occupancy[n]|{net})<=int(inv.physical.nodes[n][1]) for n,s in path) and all(n not in parent or parent[n]==(u,s) for (u,_),(n,s) in zip(path,path[1:]))
for core in data['cores']:
 failed=core['failed_connection'];selected={int(c):i for c,i in core['selection'].items()};assert failed not in selected
 assert all(i in domains[c] for c,i in selected.items()) and all(not legal(failed,i,selected) for i in domains[failed])
 for cid in selected:assert any(legal(failed,i,{c:j for c,j in selected.items() if c!=cid}) for i in domains[failed])
index=0
root=json.loads((T/'component_1.json').read_text())['result']['proof']
def visit(node,selected):
 global index
 selected={**selected,**{c:domains[c][i] for c,i in node['forced']}}
 if node['kind']=='DEAD':
  entry=data['coverage'][index];assert entry['leaf']==index;core=data['cores'][entry['core']];assert core['failed_connection']==node['empty_connection'];assert all(selected.get(int(c))==i for c,i in core['selection'].items());index+=1;return
 for child in node['children']:visit(child['proof'],{**selected,node['connection']:domains[node['connection']][child['index']]})
visit(root,{});assert index==r['covered_leaves']==len(data['coverage'])==11508 and len(data['cores'])==r['distinct_cores']==5
for p in (cp,ep):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,covered_leaves=index,distinct_cores=5,core_sizes=[len(c['selection']) for c in data['cores']],failed_connections=[c['failed_connection'] for c in data['cores']],core_coverage_counts=dict(Counter(x['core'] for x in data['coverage'])),every_core_candidate_rejected=True,every_core_member_necessary_under_fixed_paths=True,scope='Independent allleaf coverage and irreducible fixed selected-path conflict cores on certified residual domains. Removing any selected member admits at least one filtered candidate; not minimum cardinality, global graph UNSAT or route generation.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
