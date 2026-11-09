"""Join both worst-path atom segments to native sinks and final tree delays."""
import json,re,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_upstream_w16_2026-10-07';out.mkdir(exist_ok=False)
trace=ROOT/'experiments/native_resume_best_state_audit_2026-10-07';receipt=json.loads((trace/'receipt.json').read_text());bindings={str(trace/'receipt.json'):sha(trace/'receipt.json')};data={}
graph=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w16_c128/rr_graph.xml';bindings[str(graph)]=sha(graph)
xml=ET.parse(graph).getroot();locations={int(n.get('id')):tuple(int(n.find('loc').get(k,'0')) for k in ('xlow','ylow','layer','ptc')) for n in xml.find('rr_nodes') if n.get('type')=='SINK'}
for mode in ('workflow','cold'):
 base=ROOT/f'experiments/native_resume_cbrrfix_w16_m1_{mode}_2026-10-07/canonical'
 files=[base/f for f in ('design.blif','design.net','identity.jsonl','design.route','report_timing.setup.rpt')]
 for f in files:bindings[str(f)]=sha(f)
 logic={}
 for line in (base/'design.blif').read_text().replace('\\\n',' ').splitlines():
  t=line.split()
  if t and t[0]=='.names':logic[t[-1]]=t[1:-1]
 atoms={}
 for cluster in ET.parse(base/'design.net').getroot().findall('block'):
  for b in cluster.iter('block'):
   if b.get('name')!='open' and not b.findall('block'):assert b.get('name') not in atoms;atoms[b.get('name')]=cluster.get('name')
 identity={x['name']:x for x in map(json.loads,(base/'identity.jsonl').read_text().splitlines())}
 paths=physical_paths(base/'design.route');native=trace/f'w16_m1_{mode}/output.route';bindings[str(native)]=sha(native);rawpaths=physical_paths(native);assert {n:Counter(p) for n,p in paths.items() if p}=={n:Counter(p) for n,p in rawpaths.items() if p}
 nativepins={};name=None
 for line in native.read_text().splitlines():
  m=re.match(r'^Net \d+ \((.*)\)',line)
  if m:name=m[1]
  m=re.search(r'Node:\s*(\d+)\s+SINK.*Net_pin_index:\s*(\d+)',line)
  if m:nativepins[name,int(m[1])]=int(m[2])
 row=next(q for q in receipt['rows'] if q['width']==16 and q['mode']==mode)
 assert all(sha(f)==h for f,h in row['files'].items())
 delays={(x[4],int(x[5])):float(x[7])*1e9 for x in row['events'] if x[0]=='RC_BEST_DELAY' and x[1]=='pruned'}
 report=(base/'report_timing.setup.rpt').read_text().split('#Path 2')[0];points=[]
 for line in report.splitlines():
  m=re.match(r'^(\S+)\.(inpad|outpad|in|out)\[(\d+)\]\s+\([^)]*\)\s+([0-9.]+)\s+([0-9.]+)\s*$',line)
  if m:points.append((m[1],m[2],int(m[3]),float(m[4])))
 segments=[];signal=source=None
 for atom,port,bit,inc in points:
  if port=='inpad':signal=source=atom
  elif port=='out':signal=source=atom
  else:
   assert signal and ((port=='in' and signal in logic[atom]) or (port=='outpad' and atom=='out:'+signal))
   src,dst=atoms[source],atoms[atom]
   if src==dst:segments.append(dict(net=signal,source=source,sink=atom,internal=True,report_increment_ns=inc));continue
   net=identity[signal];assert net['pins'][0]['block']==src
   sinks=[p for p in net['pins'][1:] if p['block']==dst];assert len(sinks)==1;pin=sinks[0];loc=tuple(pin[k] for k in ('x','y','layer','class'))
   branch=[p for p in paths[signal] if locations[p[-1][0]]==loc];assert len(branch)==1
   rr_sink=branch[0][-1][0];nativepin=nativepins[signal,rr_sink]
   segments.append(dict(net=signal,source=source,sink=atom,internal=False,report_increment_ns=inc,native_pin=nativepin,rr_sink=rr_sink,tree_delay_ns=delays[signal,nativepin],path=branch[0]))
 data[mode]=dict(segments=segments)
# Evaluate both logical worst-path segment sets in both routed modes, using sink RR identity.
comparisons=[]
for owner in ('workflow','cold'):
 for seg in data[owner]['segments']:
  if seg['internal']:continue
  pair={}
  for mode in ('workflow','cold'):
   w=trace/f'w16_m1_{mode}/output.route';paths=physical_paths(w);branches=[p for p in paths[seg['net']] if p[-1][0]==seg['rr_sink']];assert len(branches)==1
   text=w.read_text();name=None;pin=None
   for line in text.splitlines():
    m=re.match(r'^Net \d+ \((.*)\)',line)
    if m:name=m[1]
    m=re.search(r'Node:\s*(\d+)\s+SINK.*Net_pin_index:\s*(\d+)',line)
    if m and name==seg['net'] and int(m[1])==seg['rr_sink']:pin=int(m[2])
   q=next(q for q in receipt['rows'] if q['width']==16 and q['mode']==mode);d=[x for x in q['events'] if x[0]=='RC_BEST_DELAY' and x[1]=='pruned' and x[4]==seg['net'] and int(x[5])==pin];assert len(d)==1
   pair[mode]=dict(delay_ns=float(d[0][7])*1e9,path=branches[0],pin=pin)
  comparisons.append(dict(path_owner=owner,net=seg['net'],sink=seg['sink'],rr_sink=seg['rr_sink'],resume_minus_cold_ns=pair['workflow']['delay_ns']-pair['cold']['delay_ns'],paths_equal=pair['workflow']['path']==pair['cold']['path'],modes=pair))
assert all(sha(f)==h for f,h in bindings.items())
(out/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,source_sha256=sha(Path(__file__)),worst_paths=data,comparisons=comparisons,scope='Retrospective worst-path diagnosis; unique sink-cluster join with RR sink location and native pin index. Full native tree delays; no policy tuning from target cold labels and no complete DAG timing counterfactual.'),indent=2)+'\n')
for x in comparisons:print(x['path_owner'],x['net'],x['sink'],x['paths_equal'],x['resume_minus_cold_ns'])
