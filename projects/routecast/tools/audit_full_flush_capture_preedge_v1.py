import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_flush_capture_preedge_v1_2026-10-09';S=E/'full_source_export_fixed_bus_replay_v19_2026-10-09'
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(S/n).read_bytes()
t=(D/'tb.v').read_text()
for display in json.loads((D/'added_displays.json').read_text()):assert t.count(display)==1;t=t.replace(display,'')
assert t==(S/'tb.v').read_text()
stages=json.loads((D/'stages.json').read_text());assert len(stages)==3 and all(s['exit_code']==0 for s in stages)
log=(D/'control.log').read_text();done=re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)',log);assert done
phases={'PRE':{},'POST':{}}
for line in log.splitlines():
 match=re.search(r'FLUSH_CAPTURE_(PRE|POST) cycle=\s*(\d+)',line)
 if not match:continue
 line=line.replace('\\n',' ');row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line));cycle=int(match[2]);row['cycle']=cycle;assert cycle not in phases[match[1]];phases[match[1]][cycle]=row
assert all(sorted(p)==list(range(8)) for p in phases.values())
records=[]
for cycle in range(8):
 a=phases['PRE'][cycle];b=phases['POST'][cycle];assert a['reset']==b['reset']
 for lane in ['6','7']:
  expected='0' if a['reset']=='1' else a['native_d'+lane]
  assert b['native_q'+lane]==expected,(cycle,lane,a,b)
 records.append({'cycle':cycle,'pre':a,'post':b})
out={'mismatches':int(done.group(1)),'observations':records,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','control.log']},'scope':'Actual first8 pre/post-edge D/Q/reset observations with original complete replay. Checks native reset-or-D capture per edge, not all source/native counter functions, unknown-control reachability outside trace, or Full equivalence.'}
(D/'capture_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
