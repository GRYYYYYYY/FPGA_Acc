"""Exhaustive local binary-domain observation check and four-state counterexample search."""
import json,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'experiments/briey_undefined_fanout_v1_2026-10-09';D=R/'experiments/briey_undefined_observability_v1_2026-10-09';D.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();proof=json.loads((B/'verification.json').read_text())
for p,h in proof['bindings'].items():assert sha(p)==h
cone=json.loads((B/'cone.json').read_text());cells=cone['cells'];external=cone['external_bits'];sinks=[x['bit'] for x in proof['sequential_sinks']];assert len(external)==7 and len(cells)==6 and len(sinks)==3
seeds=proof['seed_cells']
def run(values,replacements=None):
 v=dict(zip(external,values));v.update({'0':0,'1':1,'x':'x'});todo=dict(cells)
 while todo:
  ready=[n for n,c in todo.items() if all(b in v for p,bs in c['connections'].items() if p!='Y' for b in bs)];assert ready
  for n in ready:
   c=todo.pop(n);assert c['type']=='$_MUX_';w=c['connections'];a=v[w['A'][0]];b=v[w['B'][0]];s=v[w['S'][0]]
   if replacements is not None and n in seeds:a=replacements[seeds.index(n)]
   y=a if s==0 else b if s==1 else a if a==b else 'x';v[w['Y'][0]]=y
 return [v[b] for b in sinks]
cases=0
for values in itertools.product((0,1),repeat=7):
 original=run(values);assert all(v in (0,1) for v in original)
 for repl in itertools.product((0,1),repeat=3):assert run(values,repl)==original;cases+=1
counterexample=None
for values in itertools.product((0,1,'x'),repeat=7):
 original=run(values)
 if run(values,(0,0,0))!=original:counterexample=dict(external=dict(zip(external,values)),original=original,replacement_zero=run(values,(0,0,0)));break
assert counterexample is not None
report=dict(bindings={str(p):sha(p) for p in (Path(__file__).resolve(),B/'verification.json',B/'cone.json')},binary_vectors=128,replacement_comparisons=cases,binary_sink_values_always_defined=True,four_state_counterexample=counterexample,scope='Universal local binary external-boundary observation only. Four-state equivalence explicitly fails; no rewrite/admission or whole HDL sequential equivalence.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS binary',cases,'comparisons; four-state difference confirmed')
