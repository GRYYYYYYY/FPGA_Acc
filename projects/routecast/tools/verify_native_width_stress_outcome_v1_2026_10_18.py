"""Independent fixed-input/native-status and full streamed RR syntax review."""
import json,re,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 start=time.perf_counter();root=R/'experiments/prospective_native_width_stress_v1_2026-10-18';name=sys.argv[1];folder=root/name;terminal=folder/'terminal.json';t=json.loads(terminal.read_text());startup=folder/'startup.json';s=json.loads(startup.read_text());spec=R/'experiments/prospective_native_width_stress_protocol_v1_2026-10-18/protocol.json';p=json.loads(spec.read_text());job=next(x for x in p['jobs'] if f"{x['design']}_width{x['width']}"==name);assert t['command']==s['command']==job['command_without_RR_output']+['--write_rr_graph',str(folder/'rr_graph.xml')];assert t['width']==job['width'] and t['design']==job['design'];assert all(sha(k)==h for k,h in {**t['bindings'],**t['files']}.items());bindings={**t['bindings'],**t['files'],str(terminal):sha(terminal),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
 for n in ['design.blif','design.net','design.place']:
  q=folder/n;assert sha(q)==s['input_hashes'][n]==p['bindings'][str(Path(job['input_directory'])/n)];bindings[str(q)]=sha(q)
 text=(folder/'native.log').read_text();width=job['width'];command=s['command'];assert command[command.index('--max_router_iterations')+1]=='100' and command[command.index('--seed')+1]=='1' and command[command.index('--num_workers')+1]=='1' and 'RouterOpts.max_router_iterations: 100' in text
 stats=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',text);assert [list(map(int,x)) for x in stats]==t['router_stats'];real_search=len(stats)==1 and int(stats[0][1])>0 and int(stats[0][2])>0
 rows=re.findall(r'^\s*(\d+)\s+\S+\s+\S+\s+\d+\s+\S+\s+\S+\s+\S+\s+(\d+)\s+\(\s*[\d.]+%\)',text,re.M);iterations=[int(i) for i,c in rows]
 if iterations:assert iterations==list(range(1,len(iterations)+1)) and iterations[-1]<=100
 wire=re.findall(r'Wire length usage ratio ([0-9.eE+-]+) exceeds limit of ([0-9.eE+-]+), fail routing\.',text);reason='not_classified';outcome='UNLABELLED_TOOL_OR_INPUT_ERROR'
 if t['exit_status']==2 and real_search and f'Circuit is unroutable with a channel width factor of {width}.' in text and 'VPR failed to implement circuit' in text:
  outcome='OBSERVED_NATIVE_ROUTING_FAILURE_UNDER_FIXED100ITER_BUDGET'
  if wire:reason='native_initial_wirelength_abort';assert float(wire[-1][0])>float(wire[-1][1])
  elif iterations and iterations[-1]==100:reason='native_iteration_limit_with_unresolved_routing'
  else:reason='other_native_policy_failure_requires_reason_review'
 elif t['exit_status']==0 and real_search and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text:outcome='NATIVE_SUCCESS_PENDING_INDEPENDENT_PHYSICAL_CANONICAL';reason='native_FULL_success_pending_external_physical_canonical'
 assert outcome==t['status'];graph=folder/'rr_graph.xml';node_count=edge_count=0;switches=set();types=Counter();channel=None;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='channels':
   channel=dict(e.find('channel').attrib);assert int(channel['chan_width_max'])==width
   lists=[int(x.get('info')) for x in e if x.tag in ['x_list','y_list']];assert lists and min(lists)>=0 and max(lists)<=width
  elif e.tag=='switch' and parent=='switches':sid=int(e.get('id'));assert sid not in switches;switches.add(sid)
  elif e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==node_count and int(e.get('capacity'))>=0 and e.get('type') in ['SOURCE','SINK','IPIN','OPIN','CHANX','CHANY'];types[e.get('type')]+=1;node_count+=1
  elif e.tag=='edge' and parent=='rr_edges':
   u,v,sid=[int(e.get(k)) for k in ['src_node','sink_node','switch_id']];assert 0<=u<node_count and 0<=v<node_count and sid in switches;edge_count+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert channel and node_count>0 and edge_count>0;result=dict(status='independent_native_outcome_inputs_and_full_RR_reference_review_pass',bindings=bindings,name=name,design=job['design'],width=width,outcome=outcome,reason=reason,iterations_completed=len(iterations),final_reported_overused_RR_nodes=int(rows[-1][1]) if rows else None,wirelength_abort_observation=[float(x) for x in wire[-1]] if wire else None,router_stats=[list(map(int,x)) for x in stats],RR_nodes=node_count,RR_edges=edge_count,node_types=dict(types),all_exported_RR_node_edge_switch_references_valid=True,copied_inputs_equal_frozen_sources_after_run=True,not_intrinsic_unroutability_proof=True,strict_unseen_family=False,independent_route_path_capacity_canonical_admission=False,seconds=time.perf_counter()-start,scope='Observed router result under fixed configuration, independent full RR reference/input review. A failure is not graph infeasibility proof; successful routes still need separate full path/capacity/canonical validation. No estimator accuracy, mixed-label AUROC, generalization or timing gain claim.');out=folder/'independent_outcome_verification_v1.json';out.open('x').write(json.dumps(result,indent=2)+'\n');print('WIDTH_OUTCOME_REVIEW_PASS',name,outcome,reason,len(iterations),node_count,edge_count,flush=True)
if __name__=='__main__':main()
