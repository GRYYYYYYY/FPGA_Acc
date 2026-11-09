"""Isolated baseline/candidate class-bound raw route import; no rerouting or live writes."""
import pathlib,json,hashlib,shutil,os,subprocess,time,resource,xml.etree.ElementTree as ET,re,traceback
from collections import defaultdict
from rooted_canonical_route_text_v2 import NET,render,physical_sequences
from rooted_canonical_native_reload_v2 import selected_geometry
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_joint_patch_native_analysis_v2_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 O.mkdir(exist_ok=False);J=R/'experiments/mmc_branch_proposal_joint_bank_v1_2026-10-19';jp=J/'independent_verification_v1.json';j=json.loads(jp.read_text());assert j['status']=='ALL16_PROPOSAL_SUBSETS_AND_FULL115572_CONNECTION_RC_CAPACITY_STATE_VERIFIED';patchp=J/'selected_connection_patch.json';assert j['bindings'][str(patchp)]==sha(patchp);patch={int(cid):p for cid,p in json.loads(patchp.read_text()).items()};assert sorted(patch)==[8728,41689,41692]
 S=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';assert sha(S)==j['bindings'][str(S)];frame=json.loads(S.read_text());records={q['connection_id']:q for q in frame['records']};geometry=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=pathlib.Path(geometry['previous_endpoint']);metadata=json.loads(ep.read_text());C=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/canonical';cp=C/'receipt.json';receipt=json.loads(cp.read_text());canonical=receipt['rows'][0]['canonical'];source=C/'mmc';cmd=canonical['command'];binary=pathlib.Path(cmd[0]);graph=pathlib.Path(cmd[cmd.index('--read_rr_graph')+1]);arch=pathlib.Path(cmd[1]);assert sha(graph)==metadata['graph_sha256'];assert '--analysis' in cmd and '--route' not in cmd;assert (source/'design.net').read_bytes()==(source/'design.net.post_routing').read_bytes()
 sourceproof=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/independent_xml_verification_v1.json';sp=json.loads(sourceproof.read_text());bindings={str(p):sha(p) for p in [jp,patchp,S,ep,cp,sourceproof,binary,graph,arch,pathlib.Path(__file__).resolve(),R/'tools/rooted_canonical_route_text_v2.py',R/'tools/rooted_native_sink_pin_v1.py',R/'tools/rooted_canonical_native_reload_v2.py']}
 for name in ['design.blif','design.net','design.place','design.route','identity.jsonl']:
  p=source/name;assert str(p) in sp['bindings'] and sha(p)==sp['bindings'][str(p)];bindings[str(p)]=sha(p)
 memory_current=int(pathlib.Path('/sys/fs/cgroup/memory.current').read_text());memory_max=int(pathlib.Path('/sys/fs/cgroup/memory.max').read_text());assert memory_max-memory_current>64*1024**3
 write(O/'protocol.json',dict(bindings=bindings,command=cmd,arms=['control','candidate'],candidate_patch_CIDs=sorted(patch),baseline_CPD_ns=canonical['cpd_ns'],baseline_native_ignored_fixups=330,child_address_space_limit_bytes=64*1024**3,container_memory_current=memory_current,container_memory_limit=memory_max,policy='Copy exact archived canonical inputs and route. Only candidate changed NET sections reserialize from certified source paths plus selected patch, using original unique native class pin indices. Physical IPIN may differ within the same class; native import must establish all actual pin effects and a later canonical stage is required. Original VPR analysis/FULL, no rerouting or live install. Both native exits/logs retained. No CPD result forced to baseline.',scope='Old-source placement only; original zero-counter canonical gate remains separate. No new-target route, full research completion, predictor-quality, heldout or workflow gain.'))
 try:
  for arm in ['control','candidate']:
   d=O/arm;d.mkdir()
   for name in ['design.blif','design.net','design.place','design.route']:shutil.copyfile(source/name,d/name)
  native={r['name']:r for r in map(json.loads,(source/'identity.jsonl').read_text().splitlines())};affected=sorted({records[cid]['net_id'] for cid in patch});group=defaultdict(list)
  for q in records.values():
   if q['net_id'] in affected:group[q['net_id']].append(q)
  wanted=set();edgeids=set();paths={}
  for net in affected:
   ci=json.loads((J/'results.json').read_text())['answer']['selection'][str(net)];p=J/f'net_{net}_candidate_{ci}.json';assert sha(p)==j['bindings'][str(p)];bound=json.loads(p.read_text());wanted.update(bound['unique_nodes'])
   for q in group[net]:
    ids=patch[q['connection_id']]['physical_edge_ids'] if q['connection_id'] in patch else q['answer']['physical_edge_ids'];assert ids==bound['paths'][str(q['sink'])];paths[q['connection_id']]=ids;edgeids.update(ids)
  print('SELECTED_GEOMETRY_AND_PHYSICAL_EDGES_START',len(wanted),len(edgeids),flush=True);nodes,grid,classes=selected_geometry(graph,wanted);edges={};eid=0;stack=[]
  for event,e in ET.iterparse(graph,events=('start','end')):
   if event=='start':stack.append(e);continue
   parent=stack[-2].tag if len(stack)>1 else None
   if e.tag=='edge' and parent=='rr_edges':
    if eid in edgeids:edges[eid]=tuple(int(e.get(k)) for k in ['src_node','sink_node','switch_id'])
    eid+=1
   if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
   stack.pop()
  assert set(edges)==edgeids;replacement={};pin_count=0
  for net in affected:
   name=metadata['net_names'][str(net)];identity=native[name];sink_binding={}
   for p in identity['pins']:
    if p['index']>0:sink_binding.setdefault(tuple(p[k] for k in ['x','y','layer','class']),[]).append(p['index'])
   def pin(q):
    loc=nodes[q['sink']]['loc'];key=tuple(int(loc.get(k,'0')) for k in ['xlow','ylow','layer','ptc']);matches=sink_binding[key];assert len(matches)==1;return matches[0]
   lines=[f'Net {identity["net_id"]} ({name})',''];emitted=set();parents={}
   for q in sorted(group[net],key=pin):
    path=[q['source']];switches=[]
    for edge in paths[q['connection_id']]:
     u,v,s=edges[edge];assert path[-1]==u and v not in path
     if v in parents:assert parents[v]==(u,s)
     parents[v]=(u,s);path.append(v);switches.append(s)
    assert path[-1]==q['sink'];start=0
    if emitted:
     while start+1<len(path) and path[start+1] in emitted:start+=1
     assert path[start] in emitted and all(n not in emitted for n in path[start+1:-1])
    for i in range(start,len(path)):
     n=path[i];kind=nodes[n]['type'];loc=nodes[n]['loc'];lo=f"({loc['xlow']},{loc['ylow']},{loc.get('layer','0')})";hi=f"({loc['xhigh']},{loc['yhigh']},{loc.get('layer','0')})";coordinates=lo if lo==hi else lo+' to '+hi;label='Track' if kind in ['CHANX','CHANY'] else 'Class' if kind in ['SOURCE','SINK'] else 'Pin';s=switches[i] if i<len(switches) else -1;line=f"Node:\t{n}\t {kind} {coordinates} {label}: {loc['ptc']} Switch: {s}"
     if i==len(path)-1:assert kind=='SINK';line+=f' Net_pin_index: {pin(q)}';pin_count+=1
     lines.append(line);emitted.add(n)
   lines.extend(['','']);replacement[name]=lines
  original=(source/'design.route').read_text().splitlines();head=[];sections=[];current=None
  for line in original:
   m=NET.match(line)
   if m:current=[m[2],[]];sections.append(current)
   (head if current is None else current[1]).append(line)
  output=head.copy()
  for name,section in sections:output.extend(replacement.get(name,section))
  assert set(replacement)<=set(name for name,_ in sections);(O/'candidate/design.route').write_text('\n'.join(output)+'\n');assert {n:v for n,v in physical_sequences(original).items() if n not in replacement}=={n:v for n,v in physical_sequences(output).items() if n not in replacement}
  write(O/'staging.json',dict(status='RAW_EQUIVALENT_CLASS_PATCH_STAGED',affected_NETs=affected,class_bound_sink_pins=pin_count,files={str(d/name):sha(d/name) for d in [O/'control',O/'candidate'] for name in ['design.blif','design.net','design.place','design.route']}));print('RAW_EQUIVALENT_CLASS_PATCH_STAGED',affected,flush=True)
 except Exception as e:
  write(O/'staging_failure.json',dict(status='NATIVE_INPUT_STAGING_FAILED',exception_type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};rows=[]
 for arm in ['control','candidate']:
  d=O/arm;start=time.perf_counter();print('NATIVE_ANALYSIS_START',arm,flush=True)
  def limit():resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
  with (d/'native.log').open('x') as log:code=subprocess.call(cmd,cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  text=(d/'native.log').read_text();cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text);m=re.findall(r'Found (\d+) mismatches',text);f=re.findall(r'Fixed (\d+) routing traces',text);wire=re.findall(r'Total wirelength:\s*(\d+)',text);row=dict(arm=arm,exit_code=code,seconds=time.perf_counter()-start,vpr_succeeded='VPR succeeded' in text,full_check_pass='Completed routing consistency check successfully.' in text,CPD_ns=float(cpd[-1]) if cpd else None,mismatches=int(m[-1]) if m else None,fixups=int(f[-1]) if f else None,wirelength=int(wire[-1]) if wire else None,packed_netlist_post_routing_identical=(d/'design.net.post_routing').exists() and (d/'design.net').read_bytes()==(d/'design.net.post_routing').read_bytes(),files={str(p):sha(p) for p in d.iterdir() if p.is_file()});rows.append(row);write(O/'native_stages.json',rows);print({k:v for k,v in row.items() if k!='files'},flush=True)
 write(O/'receipt.json',dict(status='BOTH_NATIVE_ANALYSIS_ARMS_TERMINAL',rows=rows,source_bindings=bindings,scope='Actual import/FULL/STA outcomes retained, not yet semantic pin/physical replay admission or original-zero-counter pass.'))
if __name__=='__main__':main()
