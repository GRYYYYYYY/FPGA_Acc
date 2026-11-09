"""Exact33 original divider upper lanes have only same-lane self-hold consumers."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_original_unoptimized_proc_state_v1_2026-10-09';mf=P/'source_unoptimized.json';af=P/'constant_classes_audit.json';m=max(json.loads(mf.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));a=json.loads(af.read_text());rows=[r for r in a['records'] if r['classification']=='unreset_capture_or_guard_obligation']
consumers={}
for name,c in m['cells'].items():
 for port,bs in c['connections'].items():
  if c['port_directions'][port]=='input':
   for lane,b in enumerate(bs):consumers.setdefault(b,[]).append((name,port,lane))
outputs={b for port in m['ports'].values() if port['direction']=='output' for b in port['bits']};records=[]
for r in rows:
 q=r['bit'];hits=consumers[q]
 if len(hits)!=1:continue
 name,port,lane=hits[0];mux=m['cells'][name];
 if mux['type']!='$mux' or port not in ['A','B']:continue
 other='B' if port=='A' else 'A'
 # Other mux input can be any data; it does not introduce a consumer of oldQ.
 if mux['connections'][other][lane]==q:continue
 y=mux['connections']['Y'][lane];dest=consumers[y]
 if len(dest)!=1:continue
 ffname,ffport,fflane=dest[0];ff=m['cells'][ffname];
 if ff['type']!='$dff' or ffport!='D' or ff['connections']['Q'][fflane]!=q:continue
 
 if q in outputs or y in outputs:continue
 records.append({'q':q,'aliases':r['aliases'],'other_mux_input':mux['connections'][other][lane],'mux_cell':name,'mux_port':port,'mux_lane':lane,'mux_next_bit':y,'ff_cell':ffname,'ff_lane':fflane,'constant':r['constant'],'only_consumption':'same-lane hold mux then same-lane DFF feedback'})
assert len({r['q'] for r in records})==38
D=E/'full_original_constant_feedback_noninterference_v1_2026-10-09';D.mkdir(exist_ok=True)
out={'records':records,'count':len(records),'conclusion':'Arbitrary initial/current 38 original state bits affect only their own hold/capture feedback. No path to other state, primary outputs or memory/control inputs exists in exact original pre-opt representation. Their equality/settling is unnecessary for observable equivalence.','scope':'Exact bit-lane structural noninterference for these38 states, retaining all actual consumers. Does not establish remaining24 unreset constant states or global source/native correctness; proc representation retains original topology but is not four-state behavioral proof of whole design.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [mf,af]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['count','conclusion','scope']},indent=2))
