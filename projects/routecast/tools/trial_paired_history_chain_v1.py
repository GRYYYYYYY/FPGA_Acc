"""Fresh three-step ABBA; actual in-memory publication and all quality gates timed."""
import json,subprocess,sys,time,statistics
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from unified_rr_audit_inventory_v2 import read
from direct_retained_route_import_v1 import load
from transaction_shared_tree_ledger_v1 import TransactionLedger
from staged_place_route_transaction_v1 import PlaceRouteStore
R=Path(__file__).resolve().parents[1];E=R/'experiments';mp=R/'tools/paired_history_chain_manifest_v1.json';m=json.loads(mp.read_text());specp=R/m['spec'];spec=json.loads(specp.read_text());D=E/'paired_history_chain_v1_2026-10-09';D.mkdir(exist_ok=False)
bindings=closure([Path(__file__),*[R/c for arm in m['plans'] for step in arm['steps'] for c in step['commands']]])
bindings[str(mp)]=sha(mp);bindings[str(specp)]=sha(specp)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,manifest=m,spec=spec),indent=2)+'\n');rows=[];identities={};inputs={}
for arm in m['plans']:
 start=time.perf_counter();fp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/receipt.json';fixture=json.loads(fp.read_text());plans=fixture['plans'];bindings.update(fixture['bindings']);bindings[str(fp)]=sha(fp)
 ep0=Path(plans[0]['endpoints']);meta0=json.loads(ep0.read_text());_,_,nodes,fields,_,_=load_endpoints(ep0);inv=read(meta0['inputs']['graph']['path'],meta0['graph_sha256']);length={}
 for n,node in enumerate(nodes):
  if node.get('type') in ('CHANX','CHANY'):
   loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
 old={int(c):path for c,path in json.loads(Path(plans[0]['state']).read_text())['state'].items()};queries={q['connection_id']:q for q in meta0['connections']};store=PlaceRouteStore(TransactionLedger(old,queries,fields['capacities'],length));steps=[];codes=[]
 with (D/f"arm_{arm['arm']}.log").open('x') as log:
  for entry in arm['steps']:
   step=entry['step'];assert store.snapshot()[0]==step-1
   for command in entry['commands']:
    code=subprocess.run([sys.executable,str(R/command)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode;codes.append(code);assert code==0,(command,code)
   rp=E/entry['report'];report=json.loads(rp.read_text());assert all(sha(f)==h for f,h in report['bindings'].items());bindings.update(report['bindings']);bindings[str(rp)]=sha(rp)
   quality=report['rows'][0] if arm['mode']=='online' else report
   assert quality['native_and_canonical_connections']==[516,516] and quality['exact_model_budget_pass'] and quality['full_named_paths_preserved'] and quality['canonical_zero_counters']
   assert quality['wirelength']==spec[arm['mode']+'_expected_wire'][step-1] and quality['cpd_ns']==spec['cpd_ns'][step-1]
   native=E/entry['native'];np=native/'protocol.json';plan=json.loads(np.read_text())['plans'][0];meta=json.loads(Path(plan['endpoints']).read_text());q={x['connection_id']:x for x in meta['connections']};budgets={x['connection_id']:Fraction(*x['exact_delay_s']) for x in json.loads(Path(plan['budget']).read_text())}
   identity={k:plan[k] for k in ('step','endpoints','budget','command')}
   if step in identities:assert identities[step]==identity
   else:identities[step]=identity
   for name in ('design.blif','design.net','design.place'):
    digest=sha(native/f'step_{step}'/name);key=(step,name)
    if key in inputs:assert inputs[key]==digest
    else:inputs[key]=digest
   target,delays,_=load(native/f'step_{step}/output.route',meta,inv)
   if arm['mode']=='online':
    sp=E/entry['selection'];assert target=={int(c):tuple(tuple(x) for x in path) for c,path in json.loads(sp.read_text())['paths'].items()};bindings[str(sp)]=sha(sp)
   def validate(ledger):
    assert ledger.state==target and set(target)==set(q) and len(target)==516
    owners=defaultdict(set);parents=defaultdict(dict)
    for cid,path in ledger.state.items():
     query=q[cid];net=query['net_id'];assert path[0]==(query['source'],None) and path[-1][0]==query['sink'] and len({n for n,s in path})==len(path)
     r,c=inv.classes[inv.node_classes[query['source']]];delay=r*c/2
     for n,s in path:owners[n].add(net)
     for (u,_),(v,s) in zip(path,path[1:]):
      assert inv.arc_multiplicities.get((u,v,s))==1;nr,nc=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+nr/2)*nc+td;assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
     assert delay<=budgets[cid]
    assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in owners.items())
   epoch,prior=store.snapshot();nets={q[c]['net_id'] for c in target if target[c]!=prior.state[c] or q[c]!=prior.queries[c]};replacement={c:path for c,path in target.items() if q[c]['net_id'] in nets};store.commit(store.stage(q,replacement),validate);assert store.snapshot()[0]==step;validate(store.snapshot()[1])
   cp=D/f"arm_{arm['arm']}_step_{step}_committed.json";cp.write_text(json.dumps(dict(epoch=step,paths=store.snapshot()[1].state),indent=2)+'\n');bindings[str(cp)]=sha(cp);bindings[str(np)]=sha(np);steps.append(dict(step=step,epoch=step,quality=quality,committed=str(cp)))
 elapsed=time.perf_counter()-start;row=dict(arm=arm['arm'],mode=arm['mode'],workflow_seconds=elapsed,exit_codes=codes,steps=steps);rows.append(row);(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(dict(arm=arm['arm'],mode=arm['mode'],workflow_seconds=elapsed),flush=True)
assert all(sha(f)==h for f,h in bindings.items());online=statistics.mean(r['workflow_seconds'] for r in rows if r['mode']=='online');cold=statistics.mean(r['workflow_seconds'] for r in rows if r['mode']=='cold')
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,online_mean_seconds=online,cold_mean_seconds=cold,online_to_cold_ratio=online/cold,identical_commands_and_input_bytes=True,scope=spec),indent=2)+'\n');print(dict(online_mean_seconds=online,cold_mean_seconds=cold,ratio=online/cold),flush=True)
