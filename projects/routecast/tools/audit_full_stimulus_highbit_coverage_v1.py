"""Replay the frozen v5 generator; predicted stimulus is not a runtime trace."""
from pathlib import Path
import re,json,hashlib
root=Path(__file__).resolve().parents[1]
p=root/'experiments/full_source_export_stimulus_diagnostic_v5_2026-10-09'
s=(p/'reference.v').read_text().split(');',1)[0]
ports=[(int(w)+1 if w else 1,n) for w,n in re.findall(r'^\s*input\s+(?:reg\s+)?(?:\[(\d+):0\]\s+)?(\w+)\s*,?\s*$',s,re.M) if n not in ['clk','reset','debugReset']]
tb=(p/'tb.v').read_text()
for width,name in ports:assert name+('=rng[31];' if width==1 else '=rng;') in tb
assert "rng=32'h9b712ac3" in tb and 'for(i=0;i<128;i=i+1)' in tb
rng=0x9b712ac3;previous={n:0 for w,n in ports};values={n:[] for w,n in ports};trace=[]
for cycle in range(128):
 if cycle>=4:
  for width,n in ports:
   rng=(1664525*rng+1013904223)&0xffffffff
   previous[n]=(rng>>31)&1 if width==1 else rng&((1<<width)-1)
 trace.append({'cycle':cycle,'inputs':dict(previous),'reset':int(cycle<=2),'debugReset':int(cycle<=2)})
 for n in values:values[n].append(previous[n])
records=[{'input':n,'width':width,'distinct_values':len(set(values[n][4:])),'transitions':sum(a!=b for a,b in zip(values[n][4:],values[n][5:]))} for width,n in ports]
assert all(x['distinct_values']==2 and x['transitions']>0 for x in records if x['width']==1)
o=root/'experiments/full_stimulus_highbit_coverage_v2_2026-10-09';o.mkdir()
report={'bindings':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [Path(__file__),p/'tb.v',p/'reference.v',p/'protocol.json']},'records':records,'cycles':128,'single_bit_inputs':12,'scope':'Generator/source code replay and predicted input coverage. No runtime signal capture or protocol validity proof.'}
(o/'audit.json').write_text(json.dumps(report,indent=2)+'\n');(o/'predicted_trace.json').write_text(json.dumps(trace,indent=2)+'\n');print(json.dumps({'cycles':128,'scalar_transition_counts':{x['input']:x['transitions'] for x in records if x['width']==1}}))
