"""Independent four-arm quality, committed paths, command identity and cost arithmetic."""
import json,math,statistics
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from unified_rr_audit_inventory_v2 import read
from direct_retained_route_import_v1 import load
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'paired_optimized_chain_v1_2026-10-09';rp=D/'verification.json';r=json.loads(rp.read_text());assert all(sha(f)==h for f,h in r['bindings'].items());mp=R/'tools/paired_optimized_chain_manifest_v1.json';m=json.loads(mp.read_text());spec=json.loads((R/m['spec']).read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(mp):sha(mp)};identities={};inputs={};checked=[];inv=None
assert json.loads((D/'progress.json').read_text())==r['rows']
protocol=json.loads((D/'protocol.json').read_text());assert protocol['manifest']==m and protocol['spec']==spec
assert all(sha(f)==h for f,h in protocol['bindings'].items())
for artifact in (D/'progress.json',D/'protocol.json',*[D/f'arm_{i}.log' for i in range(4)]):
 assert artifact.is_file();bindings[str(artifact)]=sha(artifact)
assert [x['mode'] for x in r['rows']]==['online','cold','cold','online']
assert len(r['rows'])==len(m['plans'])==4
for arm,row in zip(m['plans'],r['rows']):
 assert arm['arm']==row['arm'] and arm['mode']==row['mode'] and row['workflow_seconds']>0
 assert row['exit_codes']==[0]*sum(len(s['commands']) for s in arm['steps']) and len(row['steps'])==3
 for plan,record in zip(arm['steps'],row['steps']):
  step=plan['step'];assert record['step']==record['epoch']==step
  qp=E/plan['report'];quality=json.loads(qp.read_text());assert all(sha(f)==h for f,h in quality['bindings'].items());qrow=quality['rows'][0] if arm['mode']=='online' else quality;assert qrow==record['quality']
  assert qrow['native_and_canonical_connections']==[516,516] and qrow['exact_model_budget_pass'] and qrow['full_named_paths_preserved'] and qrow['canonical_zero_counters']
  assert qrow['wirelength']==spec[arm['mode']+'_expected_wire'][step-1] and qrow['cpd_ns']==spec['cpd_ns'][step-1]
  native=E/plan['native'];np=native/'protocol.json';n=json.loads(np.read_text())['plans'][0];identity={k:n[k] for k in ('step','endpoints','budget','command')}
  if step in identities:assert identity==identities[step]
  else:identities[step]=identity
  for name in ('design.blif','design.net','design.place'):
   value=sha(native/f'step_{step}'/name);key=(step,name)
   if key in inputs:assert inputs[key]==value
   else:inputs[key]=value
  cp=Path(record['committed']);committed=json.loads(cp.read_text());assert committed['epoch']==step
  meta=json.loads(Path(n['endpoints']).read_text());queries={x['connection_id']:x for x in meta['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(Path(n['budget']).read_text())}
  if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
  paths={int(c):path for c,path in committed['paths'].items()};assert set(paths)==set(queries)==set(budgets) and len(paths)==516
  actual,_,_=load(native/f'step_{step}/output.route',meta,inv);assert actual=={c:tuple(tuple(x) for x in path) for c,path in paths.items()}
  if arm['mode']=='online':assert committed['paths']==json.loads((E/plan['selection']).read_text())['paths']
  owners=defaultdict(set);parents=defaultdict(dict)
  for cid,path in paths.items():
   query=queries[cid];net=query['net_id'];assert path[0]==[query['source'],None] and path[-1][0]==query['sink'] and len({n for n,s in path})==len(path);nr,nc=inv.classes[inv.node_classes[query['source']]];delay=nr*nc/2
   for node,switch in path:owners[node].add(net)
   for (u,_),(v,s) in zip(path,path[1:]):
    assert inv.arc_multiplicities.get((u,v,s))==1;nr,nc=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+nr/2)*nc+td;assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
   assert delay<=budgets[cid]
  assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in owners.items())
  for f in (qp,np,cp):bindings[str(f)]=sha(f)
  checked.append(dict(arm=arm['arm'],step=step,epoch=step,connections=len(paths)))
online=statistics.mean(x['workflow_seconds'] for x in r['rows'] if x['mode']=='online');cold=statistics.mean(x['workflow_seconds'] for x in r['rows'] if x['mode']=='cold');assert math.isclose(online,r['online_mean_seconds']) and math.isclose(cold,r['cold_mean_seconds']) and math.isclose(online/cold,r['online_to_cold_ratio']);assert all(sha(f)==h for f,h in bindings.items())
out=dict(bindings=bindings,checked_commits=checked,online_mean_seconds=online,cold_mean_seconds=cold,online_to_cold_ratio=online/cold,conclusion='ONLINE_COST_REGRESSION' if online>cold else 'LOWER_COST_ON_THIS_SINGLE_SEQUENCE',scope=spec)
(D/'independent_verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ('bindings','scope')})
