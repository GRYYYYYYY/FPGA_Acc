"""Exact target-dependent affine reductions; every original arm remains included."""
import json,hashlib,xml.etree.ElementTree as ET,random
from pathlib import Path
from collections import defaultdict,Counter
from aggregate_L1_affine_factorization_v1 import factorize,value
from symbolic_NET_elimination_v1 import plan
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_reduced_L1_factor_profile_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json';contract=E/'aggregate_L1_affine_factorization_contract_v1_2026-10-20/verification.json';old=E/'wbuart_candidate_elimination_profile_v1_2026-10-20/verification.json';assert all(sha(p)==h for p,h in read(contract)['bindings'].items());files=[Path(__file__),source,contract,old,R/'tools/aggregate_L1_affine_factorization_v1.py',R/'tools/symbolic_NET_elimination_v1.py'];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'status':'FROZEN_ALL72_TARGET_DEPENDENT_EXACT_AFFINE_REDUCED_FACTOR_PROFILE','rule':'For each CHANNEL with mandatory F and M optional NET memberships, abs(F+sum(b)-T) is constant+sum(b) if F>=T, constant-sum(b) if F+M<=T; otherwise keep exact nonlinear factor. Normalize each accumulated unary by subtracting its minimum and add shift to global constant. Keep every CHANNEL/NET/arm.','checks':'Exhaustive tiny contract then real original global loss == reduced loss for actual final, existing oneNET local witness and6 fixed-label-independent test assignments/arm. Independent node-term/unary/constant/table-plan verification required.','scope':'Uses native target counts expressly for retrospective diagnostic. Changes neither objective nor candidate set. Not a label-free estimator, optimizer, routing feasibility/quality proof or performance measurement.','bindings':bindings},indent=2)+'\n');graphs={};oldrows=read(old)['rows'];rows=[]
 for row in read(source)['rows']:
  ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphs[g];channels={json.loads(x)['id'] for x in Path(row['resources']).read_text().splitlines()};out=Path(row['output']);initial=defaultdict(list);final=defaultdict(list);pools=defaultdict(list)
  def support(rs):return frozenset(dest[e] for q in rs for e in q['answer']['physical_edge_ids'] if dest[e] in channels)
  def add(net,rs):
   s=support(rs)
   if s not in pools[net]:pools[net].append(s)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for net,rs in sorted(initial.items()):add(net,rs)
  for rnd in read(out/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs)
  for q in read(out/'round1.json')['records']:final[q['net_id']].append(q)
  truthall={int(n):c for n,c in read(row['truth_payload'])['node_occupancy'].items()};truth={n:truthall.get(n,0) for n in channels};f=factorize(pools,truth,channels);scopes=defaultdict(list)
  for term in f['nonlinear']:scopes[tuple(sorted(term['patterns']))].append(term['node'])
  symbolic=plan(f['cardinalities'],[*scopes,*[(n,) for n in pools]]);start={net:pools[net].index(support(rs)) for net,rs in final.items()};local={int(n):c for n,c in read(row['diagnostic_payload'])['selected'].items()};tests=[start,local,{n:0 for n in pools},{n:len(cs)-1 for n,cs in pools.items()}];rng=random.Random(20261020)
  for _ in range(4):tests.append({n:rng.randrange(len(pools[n])) for n in sorted(pools)})
  checks=[]
  for selection in tests:
   counts=Counter(n for net,cs in pools.items() for n in cs[selection[net]]);original=sum(abs(counts[n]-truth[n]) for n in channels);reduced=value(f,selection);assert original==reduced;checks.append(original)
  assert checks[0]==row['initial_L1'] and checks[1]==row['final_L1'];d=D/row['case']/row['initializer']/row['timing_policy']/row['priority'];d.mkdir(parents=True);p=d/'reduced_factors_plan.json';p.write_text(json.dumps({'factors':f,'nonlinear_scope_groups':[{'NETs':list(s),'CHANNELs':ns} for s,ns in sorted(scopes.items())],'symbolic':symbolic,'test_assignments':tests,'test_losses':checks},separators=(',',':'))+'\n');prior=next(r for r in oldrows if all(r[k]==row[k] for k in ['case','initializer','timing_policy','priority']));result={k:row[k] for k in ['case','initializer','timing_policy','priority','output','endpoint','resources','truth_payload']};result.update(payload=str(p),NETs=len(pools),CHANNELs=len(channels),constant=f['constant'],node_kind_counts=dict(Counter(t['kind'] for t in f['node_terms'])),nonlinear_factor_scopes=len(scopes),induced_width=symbolic['induced_width'],largest_bag_states=symbolic['largest_bag_states'],largest_separator_states=symbolic['largest_separator_states'],sum_bag_states=symbolic['sum_bag_states'],sum_separator_states=symbolic['sum_separator_states'],original_largest_bag_states=prior['largest_bag_states'],real_loss_identities=len(tests));rows.append(result);print(row['case'],row['initializer'],row['timing_policy'],row['priority'],symbolic['induced_width'],symbolic['largest_bag_states'],symbolic['sum_bag_states'],flush=True)
  for path in [p,out/'initial.json',out/'round1.json',out/'receipt.json',Path(row['endpoint']),Path(g),Path(row['resources']),Path(row['truth_payload']),Path(row['diagnostic_payload'])]:bindings[str(path)]=sha(path)
 assert len(rows)==72
 (D/'verification.json').write_text(json.dumps({'status':'ALL72_EXACT_AFFINE_REDUCED_LOSSES_AND_SYMBOLIC_PROFILES_COMPUTED','rows':rows,'bindings':bindings,'target_payloads_read':True,'numeric_optimizer_executed':False,'independent_verification_pending':True},indent=2)+'\n')
if __name__=='__main__':main()
