"""Full original states and every feedback event, plus source transaction parity."""
from pathlib import Path
import ast,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'experiments/sha_monotone_relax_shadow_guard_v1_2026-10-10';M=O/'model';B=R/'experiments/sha_overflow_guard_v1_2026-10-10/second_swap/model'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=[Path(__file__)];bindings={}
for base in [B,M]:
 receipt=load(base/'receipt.json');assert all(sha(p)==h for p,h in receipt['bindings'].items());assert all(sha(p)==h for p,h in receipt['files'].items());bindings.update(receipt['bindings']);bindings.update(receipt['files']);files.append(base/'receipt.json')
for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:
 assert load(M/name)==load(B/name),name;files.extend([M/name,B/name])
a,b=load(B/'receipt.json'),load(M/'receipt.json');events=0
for x,y in zip(a['rounds'],b['rounds']):
 xx={k:v for k,v in x.items() if k not in ['state_file','seconds']};yy={k:v for k,v in y.items() if k not in ['state_file','seconds']};assert xx==yy;events+=len(y['events'])
assert len(a['rounds'])==len(b['rounds'])==2 and events==4498
old=R/'tools/run_resident_overflow_guard_model_v1.py';new=R/'tools/run_monotone_relax_shadow_guard_model_v1.py'
def loops(p):
 f=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='predict');out=[]
 for n in f.body:
  if isinstance(n,ast.For):
   n.body=[s for s in n.body if not (isinstance(s,ast.Expr) and isinstance(s.value,ast.Call) and isinstance(s.value.func,ast.Attribute) and isinstance(s.value.func.value,ast.Name) and s.value.func.value.id=='cache_phases')];out.append(ast.dump(n))
 return out
assert loops(old)==loops(new);files.extend([old,new])
from array import array
from collections import Counter,defaultdict
import sys
D=O/'diagnostics.json';diag=load(D);dp=Path(diag['dependency_path']);assert sha(dp)==diag['dependency_sha256'];assert diag['dependency_itemsize']==4 and sys.byteorder=='little'
assert len(diag['rows'])==7459
vectors=[{}, {int(k):v for k,v in load(M/'round0.json')['prices'].items()}, {int(k):v for k,v in load(M/'round1.json')['prices'].items()}]
endpoint=next(Path(k) for k in b['bindings'] if k.endswith('/endpoints.json'));groups=defaultdict(list)
for q in load(endpoint)['connections']:groups[q['net_id']].append(q)
schedule=[]
for phase,nets in [(0,sorted(groups)),(1,b['rounds'][0]['affected_nets']),(2,b['rounds'][1]['affected_nets'])]:
 for net in nets:
  qs=groups[net];schedule.append((phase,qs[0]['source'],tuple(sorted({q['sink'] for q in qs}))))
history={};counts=Counter();deps=[];offset=0;witnesses=[]
with dp.open('rb') as f:
 for i,(row,expected) in enumerate(zip(diag['rows'],schedule)):
  assert (row['phase'],row['source'],tuple(row['targets']))==expected
  assert row['weight']==(0 if row['phase']==0 else 50000000)
  assert row['dependency_offset']==offset;d=array('I');d.fromfile(f,row['dependencies']);offset+=len(d)*4
  assert len(d)==len(set(d)) and all(u<91088 for u in d);deps.append(d)
  key=(row['source'],tuple(row['targets']),row['weight']);old=history.get(key);assert row['old_row']==old
  changed=[]
  if old is None:reason='NO_PRIOR_CONTEXT';assert row['old_dependencies'] is None
  else:
   prior=diag['rows'][old];oldp=vectors[prior['phase']];current=vectors[row['phase']];changed=[u for u in deps[old] if oldp.get(u,0)!=current.get(u,0)]
   assert row['old_dependencies']==len(deps[old]);assert all(oldp.get(u,0)<=current.get(u,0) for u in set(oldp)|set(current));reason='DEPENDENCY_PRICE_CHANGED' if changed else 'CERTIFICATE_VALID'
   if not changed:assert row['output_digest']==prior['output_digest']
  assert row['reason']==reason and row['changed_count']==len(changed) and row['first_changed_node']==(min(changed) if changed else None)
  counts[reason]+=1;history[key]=i
 assert not f.read(1)
assert dict(counts)==diag['counts'] and counts['NO_PRIOR_CONTEXT']==5922 and counts['DEPENDENCY_PRICE_CHANGED']+counts['CERTIFICATE_VALID']==1537
files.extend([D,dp]);metrics=dict(counts=dict(counts),independent_all7459_dependency_sets_and_monotone_price_classifications_pass=True)
bindings.update({str(p.resolve()):sha(p) for p in files})
assert all(sha(p)==h for p,h in bindings.items())
(O/'parity_verification.json').write_text(json.dumps(dict(bindings=bindings,all6273_states_floors_prices_epochs_ledgers_and_all4498_events_equal=True,complete_initial_and_feedback_loop_AST_equal=True,all7459_requests_accounted=True,metrics=metrics,model_seconds=b['total_paid_resident_seconds'],scope='Current full endogenous price and transaction parity to prior exposed SHA model. Mandatory independent XML frame/event audits separate; no native seed/fullworkflow/heldout/performance proof.'),indent=2)+'\n');print('FULL MONOTONE SHADOW PARITY AND INDEPENDENT DEPENDENCIES',events,metrics)
