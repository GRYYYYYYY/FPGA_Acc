import json,re,shutil,subprocess,os,time
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict
from audit_native_route import NET
from stream_native_route_audit import audit
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_congested_seed_2026-10-06';work=root/'work/native_congested_seed_2026-10-06';out.mkdir();work.mkdir();src=root/'work/native_search_seed_v3_2026-10-06';command=json.loads((root/'experiments/native_search_seed_v3_2026-10-06/command.json').read_text())['command'];graph=command[command.index('--read_rr_graph')+1];xml=ET.parse(graph).getroot();nodes={int(n.get('id')):(n.get('type'),n.find('loc').attrib) for n in xml.find('rr_nodes')};edges=[(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))) for e in xml.find('rr_edges')]
old={r['net_id']:r for r in map(json.loads,(root/'experiments/native_net_identity_capture_2026-10-06/original.jsonl').read_text().splitlines())};new={r['name']:r for r in map(json.loads,(root/'experiments/native_net_identity_capture_2026-10-06/synchronized.jsonl').read_text().splitlines())}
predfile=root/'experiments/multiplier_rc_repeated_sweeps_2026-10-06/mult_6x6/iteration_4_prediction.json';pred=json.loads(predfile.read_text());assert pred['physical_graph_sha256']==sha(graph);groups=defaultdict(list)
for row in pred['connections']:groups[row['net_id']].append(row)
text=(src/'seed.route').read_text();head=text[:re.search(r'^Net ',text,re.M).start()];sections={}
for oid,rows in groups.items():
 record=new[old[oid]['name']];lines=[f"Net {record['net_id']} ({record['name']})",''];emitted=set()
 for row in sorted(rows,key=lambda r:r['connection_id']):
  path=[row['source']];sw=[]
  for eid in row['physical_edge_ids']:
   u,v,s=edges[eid];assert u==path[-1];path.append(v);sw.append(s)
  assert path[-1]==row['sink'];start=0
  if emitted:
   while start+1<len(path) and path[start+1] in emitted:start+=1
   assert path[start] in emitted and all(n not in emitted for n in path[start+1:-1])
  for i in range(start,len(path)):
   nid=path[i];kind,loc=nodes[nid];x=int(loc['xlow']);y=int(loc['ylow']);layer=int(loc.get('layer','0'));ptc=int(loc['ptc']);a=f'({x},{y},{layer})';b=f"({loc['xhigh']},{loc['yhigh']},{layer})";label='Track' if kind in ('CHANX','CHANY') else 'Class' if kind in ('SOURCE','SINK') else 'Pin';line=f"Node: {nid} {kind} {a if a==b else a+' to '+b}  {label}: {ptc}  Switch: {sw[i] if i<len(sw) else -1}"
   if kind=='SINK':
    options=[p for p in record['pins'] if p['index']>0 and (p['x'],p['y'],p['layer'],p['class'])==(x,y,layer,ptc)];assert len(options)==1;line+=f" Net_pin_index: {options[0]['index']}"
   lines.append(line);emitted.add(nid)
 sections[record['net_id']]='\n'.join(lines)+'\n\n'
# Retain unrouted/ignored NET sections from complete legal seed.
for chunk in re.split(r'(?=^Net )',text,re.M)[1:]:
 m=NET.match(chunk.splitlines()[0]);nid=int(m[1]);sections.setdefault(nid,chunk)
for name in ('design.blif','design.net','design.place'):shutil.copyfile(src/name,work/name)
(work/'seed.route').write_text(head+''.join(sections[n] for n in sorted(sections)));before=audit(graph,work/'seed.route');assert len(before['connections'])==129 and before['overflow_units']>0;(out/'seed_physical.json').write_text(json.dumps(before,indent=2)+'\n')
env=os.environ.copy();env['ROUTECAST_NATIVE_SEED']=str(work/'seed.route');(out/'command.json').write_text(json.dumps({'command':command,'cwd':str(work),'seed':env['ROUTECAST_NATIVE_SEED'],'prediction_sha256':sha(predfile)},indent=2)+'\n');start=time.monotonic()
with (out/'run.log').open('w') as f:code=subprocess.run(command,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
result={'exit_code':code,'seed_overflow':before['overflow_units'],'wall_s':time.monotonic()-start,'seed_sha256':sha(work/'seed.route'),'scope':'Congested fixed-layout postroute-informed seed replay; not prospective or performance proof.'}
if code==0:
 after=audit(graph,work/'output.route');(out/'output_physical.json').write_text(json.dumps(after,indent=2)+'\n');result.update(output_overflow=after['overflow_units'],connections=len(after['connections']),output_sha256=sha(work/'output.route'))
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
