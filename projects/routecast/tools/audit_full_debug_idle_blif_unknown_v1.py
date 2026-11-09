"""Actual final BLIF idle-state preservation with unknown external boundaries."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';text=F.read_text();nodes={}
for mt in re.finditer(r'^\.names ([^\n]+)\n([^.]*)',text,re.M):
 names=mt[1].split();rows=[r.split() for r in mt[2].splitlines() if r.strip() and not r.startswith('#')];nodes[names[-1]]={'inputs':names[:-1],'rows':rows}
for d,q in [(3386,3387),(3406,3407),(3408,3409)]:assert f'.subckt $_DFF_PP0_ C=b254 D=b{d} Q=b{q} R=b255' in text
trials=[];used=set()
for state,cmd in [('0','0'),('x','0'),('0','x')]:
 vals={n:'x' for n in {x for c in nodes.values() for x in c['inputs']} if n not in nodes};vals.update({'b3387':state,'b3407':state,'b3409':state,'b115':cmd,'const0':'0','const1':'1'});visiting=set()
 def get(n):
  if n in vals:return vals[n]
  if n not in nodes:return 'x'
  assert n not in visiting,n;visiting.add(n);c=nodes[n];ins=[get(x) for x in c['inputs']];used.add(n)
  if not c['rows']:result='0'
  elif not ins:result=c['rows'][0][0]
  else:
   pol=c['rows'][0][1];assert all(r[1]==pol for r in c['rows']);poss=set()
   for bs in itertools.product(*[['0','1'] if b in ['x','z'] else [b] for b in ins]):
    hit=any(all(p=='-' or p==b for p,b in zip(pattern,bs)) for pattern,_ in c['rows']);poss.add(pol if hit else str(1-int(pol)))
   result=next(iter(poss)) if len(poss)==1 else 'x'
  visiting.remove(n);vals[n]=result;return result
 roots={n:get(n) for n in ['b3386','b3406','b3408','new_n6633']};trials.append({'FSM_bits':state,'commandValid':cmd,'roots':roots})
assert list(trials[0]['roots'].values())==['0','0','0','1'];assert any(v=='x' for v in trials[1]['roots'].values());assert any(v=='x' for v in trials[2]['roots'].values())
out={'trials':trials,'visited_nodes':sorted(used),'visited_functions':len(used),'root_tables':{n:nodes[n] for n in trials[0]['roots']},'conclusion':'Actual final BLIF reset-zero FSM and commandValid0 preserve three Dzeros with all other boundaries independentlyunknown; statezero detector n6633=1. Missing base/command guard gives unknown roots.','scope':'Final BLIF conservative independent-completion propagation and real reset subckt binding. Export LUT masks/route equivalence and actual event timing are separate; no full replay admission.','hashes':{str(F.relative_to(R)):hashlib.sha256(F.read_bytes()).hexdigest()}}
D=R/'experiments/full_debug_idle_blif_unknown_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'trials':trials,'visited_nodes':sorted(used),'visited_functions':len(used)},indent=2))
