"""Full uniqueNET channel-length accounting across native, branch and multiNET states."""
import json,xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from native_route_ledger_import_compact import physical_paths
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_repair_unique_net_wire_v1_2026-10-08';D.mkdir(exist_ok=False)
B=E/'adder_capacity_budget_branch_repair_v1_2026-10-08';M=E/'adder_capacity_budget_multinet_repair_v1_2026-10-08';bindings={}
for root in (B,M):
 p=root/'verification.json';v=json.loads(p.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
meta=json.loads((E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json').read_text());g=Path(meta['inputs']['graph']['path']);before=sha(g);length={};stack=[]
for event,node in ET.iterparse(g,events=('start','end')):
 if event=='start':stack.append(node);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if node.tag=='node' and parent=='rr_nodes':
  if node.get('type') in ('CHANX','CHANY'):
   loc=node.find('loc');length[int(node.get('id'))]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
 if (node.tag,parent) in {('node','rr_nodes'),('edge','rr_edges'),('switch','switches')}:
  stack[-2].remove(node);node.clear()
 stack.pop()
assert sha(g)==before;bindings[str(g)]=before;rows=[]
for step in range(4):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';target=json.loads(ep.read_text());queries={q['connection_id']:q for q in target['connections']};names={name:int(net) for net,name in target['net_names'].items()}
 route=g.with_name('design.route') if step==0 else E/f'native_resume_all_inventory_adder_step{step}_cold_2026-10-07/first/output.route';native=physical_paths(route)
 unions={int(names[name]):{n for path in paths for n,s in path} for name,paths in native.items()};stages={'native':unions};failures={}
 for name,root in (('branch',B),('multinet',M)):
  p=root/f'step_{step}.json';v=json.loads(p.read_text());u=defaultdict(set)
  for cid,path in v['state'].items():u[queries[int(cid)]['net_id']].update(n for n,s in path)
  stages[name]=u;failures[name]=len(v['violation_ids']);bindings[str(p)]=sha(p)
 pernet={stage:{str(net):sum(length.get(n,0) for n in ns) for net,ns in u.items()} for stage,u in stages.items()}
 totals={stage:sum(counts.values()) for stage,counts in pernet.items()};changes=[]
 assert set(pernet['native'])==set(pernet['branch'])==set(pernet['multinet'])
 for net in sorted(pernet['native'],key=int):
  if len({pernet[stage][net] for stage in pernet})>1:changes.append(dict(net_id=int(net),**{stage:pernet[stage][net] for stage in pernet}))
 out=D/f'step_{step}_wire.json';out.write_text(json.dumps(dict(per_net_unique_channel_wire=pernet,changed_nets=changes),indent=2)+'\n');bindings[str(out)]=sha(out);bindings[str(ep)]=sha(ep);bindings[str(route)]=sha(route)
 row=dict(step=step,totals=totals,branch_delta=totals['branch']-totals['native'],multinet_delta=totals['multinet']-totals['native'],budget_failures=failures);rows.append(row);print(row,flush=True)
assert all(sha(f)==h for f,h in bindings.items())
for n in ('audit_adder_repair_unique_net_wire_v1.py','native_route_ledger_import_compact.py','pre_route_endpoints.py'):
 p=R/'tools'/n;bindings[str(p)]=sha(p)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Complete node-union channel geometry length once per NET, all four steps and all states. Same physical metric, not asserted identical to printed VPR wirelength or global CPD. No native reload, quality acceptance or routing runtime gain.'),indent=2)+'\n')
