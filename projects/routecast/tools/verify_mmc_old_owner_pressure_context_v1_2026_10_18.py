"""Independent XML-capacity and regex old-owner replay of one pressure context."""
import json,sys,re,xml.etree.ElementTree as E
from pathlib import Path
from array import array
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_old_owner_pressure_context_v1_2026-10-18';sp=D/'selection.json';S=json.loads(sp.read_text());P=json.loads((D/'protocol.json').read_text());bindings={**S['bindings'],str(sp):sha(sp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=json.loads(Path(g['previous_endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];caps=array('I');stack=[]
for event,e in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='node' and parent=='rr_nodes':
  assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));stack[-2].remove(e);e.clear()
 if e.tag=='rr_nodes':break
 stack.pop()
pressure={};units={}
for case,path in P['initial_models'].items():
 f=json.loads(Path(path).read_text());pressure[case]={int(n) for n,v in f['ledger'].items() if v>caps[int(n)]};units[case]=sum(max(0,v-caps[int(n)]) for n,v in f['ledger'].items());assert units[case]==f['overflow_units']
names={ep['net_names'][str(q['net_id'])]:q['net_id'] for q in ep['connections']};owners={n:set() for values in pressure.values() for n in values};seen=set();current=None;header=re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)(.*)$');node=re.compile(r'^\s*Node:\s+(\d+)\s+')
for line in Path(g['previous_native_route']).open():
 m=header.match(line)
 if m:
  current=m[2] if not m[3].strip() else None
  if current is not None:assert current in names and current not in seen;seen.add(current)
 else:
  m=node.match(line)
  if m:
   assert current in names;n=int(m[1])
   if n in owners:owners[n].add(names[current])
assert seen==set(names);fanout=Counter(q['net_id'] for q in ep['connections']);rows=[]
for case in P['cases']:
 ip=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'staged_input_verification_v1.json';assert bindings[str(ip)]==sha(ip);dirty=set(json.loads(ip.read_text())['affected']['affected_net_ids']);witness={}
 for n in pressure[case]:
  for net in owners[n]:witness.setdefault(str(net),set()).add(n)
 expected=dirty|{int(n) for n in witness};actual=next(r for r in S['rows'] if r['case']==case);assert set(actual['net_ids'])==expected and set(actual['overused_rr_nodes'])==pressure[case] and actual['overflow_units']==units[case] and set(actual['endpoint_NET_closure'])==dirty
 assert actual['old_owner_witnesses']=={n:sorted(v) for n,v in witness.items()} and actual['NETs']==len(expected) and actual['connections']==sum(fanout[n] for n in expected);rows.append(dict(case=case,NETs=len(expected),connections=actual['connections'],overused_RR_nodes=len(pressure[case])))
assert all(sha(p)==h for p,h in bindings.items())
with (D/'independent_selection_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all3_pressure_sets_and_old_owner_NET_contexts_independently_equal=True,no_current_native_labels_used=True,scope='Independent full XML node capacities, already audited initial frame ledgers and regex old-route NET-owner replay. Old owners are candidate dependency context, not proof of actual native rerouted scope or gain.'),f,indent=2)
print('ALL3OLD OWNER PRESSURE CONTEXT SELECTIONS VERIFIED',rows,flush=True)
