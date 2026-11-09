"""Freeze old-route owner context at initial model-overused RR nodes; no target labels."""
import json,sys,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_old_owner_pressure_context_v1_2026-10-18';D.mkdir();cases=['case_01','case_02','case_03'];bindings=closure([Path(__file__)]);models={};dirty={};ledgers={};expected={}
gp=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';g=json.loads(gp.read_text());epfile=Path(g['previous_endpoint']);old=json.loads(epfile.read_text());graph=Path(old['inputs']['graph']['path']);route=Path(g['previous_native_route']);assert sha(graph)==old['graph_sha256'];names={old['net_names'][str(q['net_id'])]:q['net_id'] for q in old['connections']};assert len(names)==55300
for c in cases:
 proof=R/'experiments/mmc_multiplacement_models_v1_2026-10-18'/c/'initial_independent_verification_v1.json';v=json.loads(proof.read_text());assert v['all115572V2budgets_matched'] and all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(proof)]=sha(proof)
 p=proof.parent/'native_retained/initial.json';f=json.loads(p.read_text());assert f['graph_sha256']==old['graph_sha256'] and f['completed_connections']==f['required_connections']==115572;ledgers[c]={int(n):v for n,v in f['ledger'].items()};expected[c]=f['overflow_units'];models[c]=str(p);bindings[str(p)]=sha(p)
 p=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/c/'staged_input_verification_v1.json';v=json.loads(p.read_text());dirty[c]=set(v['affected']['affected_net_ids']);bindings[str(p)]=sha(p)
for p in [gp,epfile,graph,route]:bindings[str(p)]=sha(p)
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,cases=cases,initial_models=models,selection='One fixed context: endpoint NET closure union every accepted old physical NET whose printed route contains any RR node with initial native_retained_off modeled occupancy above original XML capacity. All RR types included. Old ownership only; no spatial radius, no target route, feedback score or label used. No parameter sweep.',scope='Exposed-case diagnostic selection; cached already audited initial forecasts are paid inputs, not a fresh end-to-end result. Old-owner candidates are not a proof of current ownership or native reroute identity. Selection needs independent originalXML and oldroute replay before feedback use.'),f,indent=2)
pressure={c:set() for c in cases};units=Counter();seen={c:set() for c in cases};stack=[]
for event,e in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='node' and parent=='rr_nodes':
  n=int(e.get('id'));cap=int(e.get('capacity'))
  for c in cases:
   if n in ledgers[c]:
    seen[c].add(n);excess=max(0,ledgers[c][n]-cap);units[c]+=excess
    if excess:pressure[c].add(n)
  stack[-2].remove(e);e.clear()
 if e.tag=='rr_nodes':break
 stack.pop()
for c in cases:assert seen[c]==set(ledgers[c]) and units[c]==expected[c]
selected={c:set(dirty[c]) for c in cases};witness={c:{} for c in cases};current=None;printed=set()
for line in route.open():
 w=line.split()
 if w and w[0]=='Net':
  current=line.split('(',1)[1].rsplit(')',1)[0] if line.rstrip().endswith(')') else None
  if current is not None:assert current in names;printed.add(current)
 elif w and w[0]=='Node:':
  assert current in names;n=int(w[1])
  for c in cases:
   if n in pressure[c]:selected[c].add(names[current]);witness[c].setdefault(str(names[current]),set()).add(n)
assert printed==set(names);fanout=Counter(q['net_id'] for q in old['connections']);rows=[]
for c in cases:
 row=dict(case=c,overused_rr_nodes=sorted(pressure[c]),overflow_units=units[c],endpoint_NET_closure=sorted(dirty[c]),net_ids=sorted(selected[c]),NETs=len(selected[c]),connections=sum(fanout[n] for n in selected[c]),old_owner_witnesses={n:sorted(v) for n,v in witness[c].items()});rows.append(row);print('OWNER PRESSURE CONTEXT',c,row['NETs'],row['connections'],len(pressure[c]),units[c],flush=True)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'selection.json').open('x') as f:json.dump(dict(bindings={**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},rows=rows,independent_selection_audit_pending=True,no_current_native_route_or_quality_values_read=True),f,indent=2)
