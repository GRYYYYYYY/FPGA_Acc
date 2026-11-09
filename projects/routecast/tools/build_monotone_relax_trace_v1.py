"""Record successful-relax price destinations and every post-search verification read."""
from pathlib import Path
import ast,json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];O=R/'build/monotone_relax_trace_v1_2026-10-10';O.mkdir(exist_ok=True)
tree=ast.parse((R/'tools/build_price_read_trace_v3.py').read_text());helper=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helper' for t in n.targets)));inputs={};outputs={};changes={}
for name in ['tree_workspace_radix_v3.cpp','tree_workspace_radix_stats_v4.cpp','bidirectional_workspace_v2.cpp']:
 p=R/'tools/soft_demand_cpp'/name;original=p.read_text();s=original;edits=[]
 if name.startswith('tree_'):
  edits=[('if(next<d[v]){','if(next<d[v]){rc_price_read(price,v);'),('if(next<w->d[v]){','if(next<w->d[v]){rc_price_read(price,v);')]
 else:
  edits=[('if(value<w->distance[s][v]){','if(value<w->distance[s][v]){rc_price_read(price,destination);')]+[('price['+x+']','rc_price_read(price,'+x+')') for x in ['w->dest[x]','w->dest[e]','v']]
 for before,after in edits:assert s.count(before)==1,(name,before);s=s.replace(before,after)
 restored=s
 for before,after in reversed(edits):restored=restored.replace(after,before)
 assert restored==original
 changes[name]=edits;inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();(O/name).write_text((helper if name!='tree_workspace_radix_stats_v4.cpp' else '')+s)
for name,lib in [('tree_workspace_radix_v3.cpp','forward.so'),('bidirectional_workspace_v2.cpp','bidi.so')]:
 c=subprocess.run(['g++','-std=c++17','-O3','-shared','-fPIC',str(O/name),'-o',str(O/lib)],capture_output=True,text=True);(O/(lib+'.build.log')).write_text(c.stdout+c.stderr);assert c.returncode==0,c.stderr
for p in [*O.glob('*.cpp'),*O.glob('*.so')]:outputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
inputs[str(R/'tools/build_price_read_trace_v3.py')]=hashlib.sha256((R/'tools/build_price_read_trace_v3.py').read_bytes()).hexdigest()
(O/'receipt.json').write_text(json.dumps(dict(inputs=inputs,outputs=outputs,source_reversible=True,edits=changes,scope='Standalone128 monotone certificate instrumentation; overflow envelope must be separately validated. No skip or native64 implementation.'),indent=2)+'\n');print('MONOTONE RELAX TRACE BUILD PASS')
