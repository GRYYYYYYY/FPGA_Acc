"""Descriptive exact-decimal path lattice versus frozen candidate budgets, all pins/rounds."""
import json
from math import lcm
from pathlib import Path
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10';T=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10'
proofs=[O/'verification.json',O/'pin_identity_audit_v1.json',O/'common_state_projection_verification_v1.json',T/'independent_audits_verification.json'];bindings={}
for p in proofs:
 d=json.loads(p.read_text());assert all(sha(n)==h for n,h in d['bindings'].items());bindings.update(d['bindings']);bindings[str(p)]=sha(p)
ep=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';e=json.loads(ep.read_text());graph=Path(e['inputs']['graph']['path']);ids,classes,switches,digest=read(graph);assert digest==e['graph_sha256'] and all(r==0 and c==0 for r,c in classes)
scale=lcm(*(delay.denominator for resistance,delay in switches.values()));assert scale==10**18
inc={sid:int(delay*scale) for sid,(resistance,delay) in switches.items()};assert all((delay*scale).denominator==1 for resistance,delay in switches.values())
manifest=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';queries={}
for line in manifest.read_text().splitlines():
 f=line.split()
 if f[0]=='Q':cid,net,pin,source,sink=map(int,f[1:]);queries[net,pin]=(cid,source,sink)
records={r['connection_id']:r for r in json.loads((T/'model/initial.json').read_text())['records']};assert len(records)==len(queries)==115572
rows=[]
for iteration in range(1,22):
 trees={};pins={}
 with (O/'states'/f'round_{iteration}.tsv').open() as s:
  for line in s:
   f=line.split()
   if f[0]!='T':continue
   net,n,parent,switch=int(f[1]),int(f[2]),int(f[3]),int(f[4]);index=int(f[6]);tree=trees.setdefault(net,{})
   if n in tree:assert tree[n]==(parent,switch)
   tree[n]=(parent,switch)
   if index>=1:pins[net,index]=n
 raw={net:{n:0 for n,(p,sw) in tree.items() if p==-1} for net,tree in trees.items()};violations=0;maximum_excess=0;examples=[]
 for key,(cid,source,sink) in queries.items():
  net,pin=key;r=records[cid];assert (r['net_id'],r['source'],r['sink'])==(net,source,sink);assert pins[key]==sink
  tree=trees[net];memo=raw[net];trail=[];u=sink;seen=set()
  while u not in memo:
   assert u not in seen;seen.add(u);parent,sw=tree[u];assert parent>=0;trail.append((u,sw));u=parent
  value=memo[u]
  for n,sw in reversed(trail):value+=inc[sw];memo[n]=value
  value=memo[sink];excess=value-r['budget_integer']
  if excess>0:
   violations+=1;maximum_excess=max(maximum_excess,excess)
   if len(examples)<10:examples.append({'connection_id':cid,'raw_integer':value,'budget_integer':r['budget_integer']})
 rows.append({'iteration':iteration,'connections':len(queries),'candidate_budget_violations':violations,'maximum_excess_integer':maximum_excess,'examples':examples});print('BUDGET DIAGNOSTIC',iteration,violations,flush=True)
bindings.update({str(graph):digest,str(ep):sha(ep),str(Path(__file__).resolve()):sha(Path(__file__)),str(R/'tools/buffered_rc_node_classes.py'):sha(R/'tools/buffered_rc_node_classes.py')});assert all(sha(n)==h for n,h in bindings.items())
f=O/'candidate_budget_diagnostic_v1.json';assert not f.exists();f.write_text(json.dumps({'bindings':bindings,'scale':scale,'rows':rows,'scope':'Exact serialized-decimal path delay lattice versus independently audited frozen candidate budgets. Native router is not constrained by these budgets. Violations descriptive, not native invalidity, timing slack, causal hotspot explanation, heldout or QoR proof.'},indent=2)+'\n')
