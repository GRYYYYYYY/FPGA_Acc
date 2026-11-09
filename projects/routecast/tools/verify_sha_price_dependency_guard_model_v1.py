"""Full original states and every feedback event, plus source transaction parity."""
from pathlib import Path
import ast,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'experiments/sha_price_dependency_guard_model_v1_2026-10-10';M=O/'model';B=R/'experiments/sha_overflow_guard_v1_2026-10-10/second_swap/model'
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
old=R/'tools/run_resident_overflow_guard_model_v1.py';new=R/'tools/run_price_dependency_overflow_guard_model_v1.py'
def loops(p):
 f=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='predict');out=[]
 for n in f.body:
  if isinstance(n,ast.For):
   n.body=[s for s in n.body if not (isinstance(s,ast.Expr) and isinstance(s.value,ast.Call) and isinstance(s.value.func,ast.Attribute) and isinstance(s.value.func.value,ast.Name) and s.value.func.value.id=='cache_phases')];out.append(ast.dump(n))
 return out
assert loops(old)==loops(new);files.extend([old,new,M/'cache_metrics.json'])
metrics=load(M/'cache_metrics.json');assert len(metrics['phases'])==3
last=metrics['phases'][-1];assert last['stats'].get('hits',0)+last['stats']['misses']==7459
assert all(p['dependency_items']<=1048576 and p['output_items']<=262144 and p['entries']<=4096 for p in metrics['phases'])
bindings.update({str(p.resolve()):sha(p) for p in files})
assert all(sha(p)==h for p,h in bindings.items())
(O/'parity_verification.json').write_text(json.dumps(dict(bindings=bindings,all6273_states_floors_prices_epochs_ledgers_and_all4498_events_equal=True,complete_initial_and_feedback_loop_AST_equal=True,all7459_requests_accounted=True,metrics=metrics,model_seconds=b['total_paid_resident_seconds'],scope='Current full endogenous price and transaction parity to prior exposed SHA model. Mandatory independent XML frame/event audits separate; no native seed/fullworkflow/heldout/performance proof.'),indent=2)+'\n');print('FULL MODEL PARITY',events,last)
