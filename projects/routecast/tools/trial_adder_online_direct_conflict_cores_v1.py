"""Greedy irreducible selected-path conflict cores covering certified DFS dead leaves."""
import json,time
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';T=E/'adder_online_direct_joint_net_components_v5_2026-10-09';B=E/'adder_online_direct_joint_net_search_v5_2026-10-09';D=E/'adder_online_direct_conflict_cores_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();vp=E/'adder_online_direct_joint_net_component_verification_v5_2026-10-09/verification.json';v=json.loads(vp.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());q={x['connection_id']:x for x in meta['connections']};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);bank={int(c):opts for c,opts in json.loads((B/'step_3.json').read_text())['bank'].items()};decomp=json.loads((T/'decomposition.json').read_text());domains={int(c):ids for c,ids in decomp['domains'].items()};proof=json.loads((T/'component_1.json').read_text())['result']['proof'];cores=[];lookup={};coverage=[]
def rejects(failed,selection):
 owners=defaultdict(set);parents=defaultdict(dict)
 for cid,index in selection.items():
  net=q[cid]['net_id'];path=bank[cid][index]['path']
  for n,s in path:owners[n].add(net)
  for (u,_),(n,s) in zip(path,path[1:]):assert n not in parents[net] or parents[net][n]==(u,s);parents[net][n]=(u,s)
 net=q[failed]['net_id'];reasons=[]
 for i in domains[failed]:
  path=bank[failed][i]['path'];bad=[dict(kind='CAPACITY',node=n,owners=sorted(owners[n]|{net})) for n,s in path if len(owners[n]|{net})>int(inv.physical.nodes[n][1])]
  bad.extend(dict(kind='PARENT',node=n,parent=[u,s],existing_parent=list(parents[net][n])) for (u,_),(n,s) in zip(path,path[1:]) if n in parents[net] and parents[net][n]!=(u,s))
  reasons.append(dict(index=i,reasons=bad))
 return reasons
def walk(node,selected):
 selected={**selected,**{c:domains[c][i] for c,i in node['forced']}}
 if node['kind']=='DEAD':
  failed=node['empty_connection'];assert all(x['reasons'] for x in rejects(failed,selected));relevant={n for i in domains[failed] for n,s in bank[failed][i]['path']};core={c:i for c,i in selected.items() if relevant&{n for n,s in bank[c][i]['path']}}
  assert all(x['reasons'] for x in rejects(failed,core))
  for cid in sorted(list(core)):
   reduced={c:i for c,i in core.items() if c!=cid}
   if all(x['reasons'] for x in rejects(failed,reduced)):core=reduced
  key=(failed,tuple(sorted(core.items())))
  if key not in lookup:
   lookup[key]=len(cores);cores.append(dict(failed_connection=failed,selection={str(c):i for c,i in core.items()},candidate_rejections=rejects(failed,core)))
  coverage.append(dict(leaf=len(coverage),core=lookup[key]));return
 assert node['kind']=='BRANCH'
 for child in node['children']:walk(child['proof'],{**selected,node['connection']:domains[node['connection']][child['index']]})
walk(proof,{});assert len(coverage)==len(v['rows'][0]['dead_leaves']);p=D/'cores.json';p.write_text(json.dumps(dict(cores=cores,coverage=coverage),indent=2)+'\n');bindings[str(p)]=sha(p);assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,covered_leaves=len(coverage),distinct_cores=len(cores),core_sizes=sorted({len(c['selection']) for c in cores}),component_seconds=time.perf_counter()-start,scope='Greedy irreducible selected-path cores, not minimum cores or global UNSAT. Every filtered candidate rejected under a subset of certified leaf assignments; subsequent search still required. No path generation/native/performance claim.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
