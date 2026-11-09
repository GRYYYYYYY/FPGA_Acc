"""Serialize complete dirty-NET capacity candidates and run original VPR FULL analysis."""
import json,re,shutil,subprocess,time,os
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';parent=base/'native_complete_joint_capacity_rc_2026-10-06';proof=json.loads((parent/'verification.json').read_text());receipt=json.loads((parent/'receipt.json').read_text());assert sha(parent/'receipt.json')==proof['receipt_sha256'];cohort=json.loads((base/'native_complete_move_queries_2026-10-06/adder_0.json').read_text());assert all(sha(p)==h for p,h in cohort['inputs_sha256'].items());reference=root/'work/native_candidate_resource_frames_2026-10-06/adder';prior=json.loads((base/'native_candidate_resource_frames_2026-10-06/receipt.json').read_text())['results'][1];assert all(sha(p)==h for p,h in prior['inputs_sha256'].items());graph=Path(next(p for p in cohort['inputs_sha256'] if p.endswith('rr_graph.xml')));xml=ET.parse(graph).getroot();nodes={int(n.get('id')):(n.get('type'),dict(n.find('loc').attrib)) for n in xml.find('rr_nodes')};edges=[(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))) for e in xml.find('rr_edges')];nonconfig={int(s.get('id')) for s in xml.find('switches') if s.get('type') in ('buffer','short')};forced=defaultdict(list)
for u,v,s in edges:
 if s in nonconfig:forced[u].append(v)
netre=re.compile(r'^\s*Net\s+(\d+)\s+\(');sections={};head=[];net=None
for line in (reference/'seed.route').read_text().splitlines():
 m=netre.match(line)
 if m:net=int(m[1]);sections[net]=[]
 (head if net is None else sections[net]).append(line)
place_lines=(reference/'state_0.place').read_text().splitlines();blockrows={int(line.split()[-1].lstrip('#')):i for i,line in enumerate(place_lines) if line.strip() and not line.startswith(('#','Netlist','Array'))}
out=base/'native_complete_capacity_native_import_v2_2026-10-06';out.mkdir(exist_ok=True);work=root/'work/native_complete_capacity_native_import_v2_2026-10-06';work.mkdir(exist_ok=True);binary=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_vpr/vpr/vpr';arch=prior['command'][1];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};results=[]
for row in receipt['results']:
 index=row['pair_index'];p=parent/f'pair_{index}.json';assert sha(p)==row['sha256'];data=json.loads(p.read_text());assert data['failure'] is None and data['completed_connections']==data['required_connections'] and not data['overflow_units'] and not data['multi_parent_nodes'];cwd=work/str(index);cwd.mkdir(exist_ok=True);groups=defaultdict(list)
 for q in data['records']:groups[q['net_id']].append(q)
 lines=place_lines.copy();a,b=map(blockrows.get,data['pair']);aa=lines[a].split();bb=lines[b].split();aa[1:5],bb[1:5]=bb[1:5],aa[1:5];lines[a]='\t'.join(aa);lines[b]='\t'.join(bb);(cwd/'design.place').write_text('\n'.join(lines)+'\n')
 for name in ('design.net','design.blif'):shutil.copyfile(reference/name,cwd/name)
 routehead=head.copy();routehead[0]='Placement_File: design.place Placement_ID: SHA256:'+sha(cwd/'design.place');serialized=routehead.copy();forced_missing=[];sinkcount=0
 for net,section in sections.items():
  if net not in groups:
   for line in section:
    if line.startswith('Block '):
     tokens=line.split();block=int(tokens[2].strip('(#)'));loc=lines[blockrows[block]].split();tokens[4]=f'({loc[1]},{loc[2]},{loc[4]})';line=' '.join(tokens)
    serialized.append(line)
   continue
  serialized.extend([section[0],'']);emitted=set()
  for q in sorted(groups[net],key=lambda q:q['pin_index']):
   path=[q['source']];sw=[]
   for eid in q['result']['physical_edge_ids']:
    u,v,s=edges[eid];assert u==path[-1];path.append(v);sw.append(s)
   assert path[-1]==q['sink'];start=0
   if emitted:
    while start+1<len(path) and path[start+1] in emitted:start+=1
    assert path[start] in emitted and all(n not in emitted for n in path[start+1:-1])
   for i in range(start,len(path)):
    n=path[i];kind,loc=nodes[n];xyz=lambda x,y:f"({loc[x]},{loc[y]},{loc.get('layer','0')})";lo=xyz('xlow','ylow');hi=xyz('xhigh','yhigh');coords=lo if lo==hi else lo+' to '+hi;label='Track' if kind in ('CHANX','CHANY') else 'Class' if kind in ('SOURCE','SINK') else 'Pin';s=sw[i] if i<len(sw) else -1;line=f"Node:\t{n}\t {kind} {coords} {label}: {loc['ptc']} Switch: {s}"
    if i==len(path)-1:assert kind=='SINK';line+=f" Net_pin_index: {q['pin_index']}";sinkcount+=1
    serialized.append(line);emitted.add(n)
  forced_missing.extend({'net':net,'source':n,'sink':v} for n in emitted for v in forced[n] if v not in emitted);serialized.extend(['',''])
 assert sinkcount==data['required_connections'];(cwd/'design.route').write_text('\n'.join(serialized)+'\n');cmd=[str(binary),arch,'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',str(graph),'--route_chan_width','300','--num_workers','1','--check_route','full'];start=time.perf_counter()
 with (cwd/'import.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 log=(cwd/'import.log').read_text();cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log);results.append({'pair_index':index,'required_connections':sinkcount,'missing_forced_nodes':forced_missing,'exit_code':code,'native_success':code==0 and 'VPR succeeded' in log,'cpd_ns':float(cpd[1]) if cpd else None,'wall_s':time.perf_counter()-start,'command':cmd,'cwd':str(cwd),'sha256':{str(cwd/n):sha(cwd/n) for n in ('design.net','design.blif','design.place','design.route','import.log')}});print(index,code,results[-1]['native_success'],results[-1]['cpd_ns'],len(forced_missing),flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'source_sha256':sha(Path(__file__)),'binary_sha256':sha(binary),'architecture_sha256':sha(arch),'graph_sha256':sha(graph),'parent_verification_sha256':sha(parent/'verification.json'),'scope':'Fresh original VPR analysis with FULL route check, complete dirty-NET serialization and retained unchanged NETs. No rerouting or end-to-end speed claim; postroute pin fixups must be reviewed.'},indent=2)+'\n')
