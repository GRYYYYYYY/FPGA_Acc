"""Frozen RR-input-only all-cut profiles; never read new routing outcomes."""
import json,sys,time,os,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import extract,sha
from source_binding_v2 import closure
from RR_separator_capacity_bound_v1 import profile
ROOT=R/'experiments/width_stress_RR_separator_profiles_v1_2026-10-18'
NATIVE=R/'experiments/prospective_native_width_stress_v1_2026-10-18'

def alive(identity):
 try:s=Path('/proc',str(identity['pid']),'stat').read_text().split(') ',1)[1].split()
 except FileNotFoundError:return False
 return s[19]==identity['startticks'] and s[0]!='Z'

def ready(folder):
 if not (folder/'rr_graph.xml').exists() or not (folder/'startup.json').exists() or not (folder/'native.log').exists():return False
 # Stop before routing statistics or terminal output, even for finished cases.
 with (folder/'native.log').open() as f:
  for line in f:
   if 'Initializing router criticalities took' in line:return True
 return False

def signature(e):
 loc=e.find('loc');return (e.get('type'),int(e.get('capacity')),*(int(loc.get(k,'0')) for k in ['xlow','ylow','xhigh','yhigh','layer','ptc']))

def old_signatures(graph,wanted):
 answer={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   nid=int(e.get('id'))
   if nid in wanted:answer[nid]=signature(e)
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert set(answer)==wanted;return answer

def read_graph(graph,wanted):
 caps=array('I');coordinates={k:array('I') for k in ['xlow','xhigh','ylow','yhigh']};us=array('I');vs=array('I');signatures={};switches=set();stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='switch' and parent=='switches':sid=int(e.get('id'));assert sid not in switches;switches.add(sid)
  elif e.tag=='node' and parent=='rr_nodes':
   nid=int(e.get('id'));assert nid==len(caps);caps.append(int(e.get('capacity')));loc=e.find('loc')
   for k,values in coordinates.items():values.append(int(loc.get(k)))
   if nid in wanted:signatures[nid]=signature(e)
  elif e.tag=='edge' and parent=='rr_edges':
   u,v,sid=[int(e.get(k)) for k in ['src_node','sink_node','switch_id']];assert 0<=u<len(caps) and 0<=v<len(caps) and sid in switches;us.append(u);vs.append(v)
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert set(signatures)==wanted;return caps,coordinates,us,vs,signatures

def main():
 spec=R/'experiments/width_stress_RR_separator_protocol_v1_2026-10-18/protocol.json';p=json.loads(spec.read_text());assert all(sha(k)==h for k,h in p['bindings'].items());ROOT.mkdir();stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(ROOT/'live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=stat[19]))+'\n');bindings={**closure([Path(__file__)]),str(spec):sha(spec)};producer=json.loads((NATIVE/'live_process.json').read_text());prior={};rows=[]
 for name in p['cases']:
  (ROOT/'supervision.json').write_text(json.dumps(dict(status='waiting_RR_graph_write_and_native_initialization_marker_only',case=name,producer=producer,complete_cases=len(rows)),indent=2)+'\n');folder=NATIVE/name
  while not ready(folder):
   if not alive(producer):raise RuntimeError('Required RR/source readiness missing after native producer terminal; no routed fallback')
   time.sleep(3)
  tick=time.perf_counter();design=name.split('_width')[0];source=p['approved_prior_physical_NET_identity'][design];ap=Path(source['approved_endpoints']);approved=json.loads(ap.read_text());partition=Path(source['whole_NET_ignore_partition']);v=json.loads(partition.read_text());assert v['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'];assert all(sha(k)==h for k,h in v['bindings'].items());graph=folder/'rr_graph.xml';startup=folder/'startup.json';native_startup=json.loads(startup.read_text());graph_before=sha(graph)
  for kind,n in [('net','design.net'),('place','design.place')]:assert sha(folder/n)==native_startup['input_hashes'][n]==approved['inputs'][kind]['sha256']
  if design not in prior:
   oldgraph=Path(approved['inputs']['graph']['path']);assert sha(oldgraph)==approved['graph_sha256'];wanted={q[k] for q in approved['connections'] for k in ['source','sink']};prior[design]=old_signatures(oldgraph,wanted)
  family_setup=time.perf_counter()-tick;out=ROOT/name;out.mkdir();(ROOT/'supervision.json').write_text(json.dumps(dict(status='extracting_current_physical_endpoints_from_graph_NET_place_only',case=name,complete_cases=len(rows)),indent=2)+'\n');tick=time.perf_counter();ep,report=extract(folder/'design.net',folder/'design.place',graph,source['clock_policy']);endpoint_seconds=time.perf_counter()-tick;assert len(ep['connections'])==v['all_queries'];approved_byid={q['connection_id']:q for q in approved['connections']};names={approved['net_names'][str(q['net_id'])] for q in approved['connections']};filtered=[q for q in ep['connections'] if ep['net_names'][str(q['net_id'])] in names];assert {q['connection_id'] for q in filtered}==set(approved_byid) and len(filtered)==v['physical_queries'];ep['original_connection_count']=len(ep['connections']);ep['native_ignored_connection_count']=len(ep['connections'])-len(filtered);ep['connections']=filtered;ep['native_demand_policy']='Same packed NET/place and archived exhaustive wholeNET ignored partition, no new routing outcome input';ep['inputs']['prior_ignore_partition']={'path':str(partition),'sha256':sha(partition)};epfile=out/'endpoints.json';epfile.write_text(json.dumps(ep,separators=(',',':'))+'\n');(out/'pin_mapping_report.json').write_text(json.dumps(report,separators=(',',':'))+'\n');wanted={q[k] for q in filtered for k in ['source','sink']};tick=time.perf_counter();caps,coords,us,vs,signatures=read_graph(graph,wanted);RR_seconds=time.perf_counter()-tick
  for q in filtered:
   old=approved_byid[q['connection_id']];assert ep['net_names'][str(q['net_id'])]==approved['net_names'][str(old['net_id'])]
   for role in ['source','sink']:assert signatures[q[role]]==prior[design][old[role]]
  terminals=defaultdict(set)
  for q in filtered:terminals[q['net_id']].update([q['source'],q['sink']])
  assert len(terminals)==len(names);case_bindings={**bindings,str(ap):sha(ap),str(partition):sha(partition),str(graph):graph_before,str(startup):sha(startup),str(epfile):sha(epfile),str(out/'pin_mapping_report.json'):sha(out/'pin_mapping_report.json')};profiles={};profile_seconds={};(ROOT/'supervision.json').write_text(json.dumps(dict(status='computing_frozen_all_x_y_separator_profiles',case=name,complete_cases=len(rows)),indent=2)+'\n')
  for axis in ['x','y']:
   tick=time.perf_counter();answer=profile(coords[axis+'low'],coords[axis+'high'],zip(us,vs),caps,terminals);profile_seconds[axis]=time.perf_counter()-tick
   for part in ['lower','upper']:
    payload=out/f'{axis}_{part}.u32';payload.write_bytes(answer[part].tobytes());case_bindings[str(payload)]=sha(payload)
   intervals=out/f'{axis}_NET_intervals.json';intervals.write_text(json.dumps(answer['NET_intervals'],separators=(',',':'))+'\n');case_bindings[str(intervals)]=sha(intervals);profiles[axis]=dict(cuts=answer['cuts'],any_capacity_infeasibility_certificate_pending_independent_review=answer['any_capacity_infeasibility_certificate'],edge_count=answer['edge_count'])
  assert sha(graph)==graph_before;assert all(sha(folder/n)==native_startup['input_hashes'][n] for n in ['design.net','design.place']);result=dict(status='real_RR_separator_profiles_complete_independent_literal_review_pending',bindings=case_bindings,name=name,design=design,physical_connections=len(filtered),physical_NETs=len(terminals),all_current_SOURCE_SINK_signatures_equal_admitted_same_NET_place=True,RR_nodes=len(caps),RR_edges=len(us),array_byteorder=sys.byteorder,profiles=profiles,costs=dict(source_identity_and_prior_setup_seconds=family_setup,current_endpoint_extraction_seconds=endpoint_seconds,RR_coordinate_edge_load_seconds=RR_seconds,axis_profile_seconds=profile_seconds),scope='Input-only necessary-bound candidate profiles. Native terminal outcomes/statistics/final routes not consumed. No real infeasibility certificate admitted until independent literal separator and forcing-demand review. No routability guarantee, forecast accuracy, unseen-family or gain claim.');pp=out/'profiles.json';pp.write_text(json.dumps(result,indent=2)+'\n');row=dict(name=name,RR_nodes=len(caps),RR_edges=len(us),physical_NETs=len(terminals),positive_cut_candidates={a:sum(x['excess']>0 for x in profiles[a]['cuts']) for a in ['x','y']},profile=str(pp));rows.append(row);(ROOT/'stages.json').write_text(json.dumps(rows,indent=2)+'\n');print('REAL_RR_SEPARATOR_PROFILE_DONE',json.dumps(row),flush=True)
 (ROOT/'results.json').write_text(json.dumps(dict(status='all4_RR_separator_profiles_complete_independent_review_pending',bindings=bindings,cases=rows),indent=2)+'\n');(ROOT/'supervision.json').write_text(json.dumps(dict(status='all4_input_only_profiles_complete',cases=4),indent=2)+'\n')
if __name__=='__main__':main()
