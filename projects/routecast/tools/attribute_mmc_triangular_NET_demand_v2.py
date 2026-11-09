"""Full per-NET paired outcome attribution; physical edges read independently from original XML."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
O=R/'experiments/mmc_triangular_span_NET_attribution_v2_2026-10-09';assert not O.exists()
B=R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09/seed/model/mmc';C=R/'experiments/mmc_triangular_span_v9_2026-10-09/model'
bindings=closure([Path(__file__)])
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
for p,gate in [(B.parents[2]/'verification.json','all_cases_both_complete_arms_authenticated'),(C.parent/'verification.json','complete_candidate_physical_and_events_pass')]:
 r=load(p);assert r[gate] and all(sha(k)==h for k,h in r['bindings'].items())
inputs=[]
for folder in [B,C]:
 receipt=load(folder/'receipt.json');assert all(sha(k)==h for field in ['bindings','files'] for k,h in receipt[field].items())
 states={frame:load(folder/(frame+'.json')) for frame in ['initial','round0','round1','sketch']}
 groups=defaultdict(list)
 for rec in states['sketch']['records']:groups[rec['net_id']].append(rec)
 status={net:['NOT_AFFECTED','NOT_AFFECTED'] for net in groups}
 for index,row in enumerate(receipt['rounds']):
  assert index==row['round_index']
  for event in row['events']:status[event['net_id']][index]=event['status']
 inputs.append((groups,status,states))
assert set(inputs[0][0])==set(inputs[1][0]) and inputs[0][2]['initial']==inputs[1][2]['initial']
ep=load(R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09/seed/demand/mmc/endpoints.json');graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=sha(graph)
# Source/destination arrays preserve original edge ordinal; channel class and span from original node XML.
sources=array('Q');dest=array('Q');classes=array('b');spans=array('Q');caps=array('Q');segments={};stack=[]
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='segment' and parent=='segments':segments[int(e.get('id'))]=dict(e.attrib)
 if e.tag=='node' and parent=='rr_nodes':
  assert int(e.get('id'))==len(classes);kind=e.get('type');loc=e.find('loc');seg=e.find('segment');sid=int(seg.get('segment_id')) if kind in ['CHANX','CHANY'] else -1
  assert sid in [-1,0,1];classes.append(sid if kind=='CHANX' else sid+2 if kind=='CHANY' else -1);caps.append(int(e.get('capacity')));spans.append(max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1)
 elif e.tag=='edge' and parent=='rr_edges':sources.append(int(e.get('src_node')));dest.append(int(e.get('sink_node')))
 if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')]:stack[-2].remove(e);e.clear()
 stack.pop()
assert sha(graph)==ep['graph_sha256'] and len(sources)==len(dest)==8097539 and len(classes)==904438
assert segments[0]['name']=='L4' and segments[0]['length']=='4' and segments[1]['name']=='L16' and segments[1]['length']=='16'
def owned(recs):
 nodes=set()
 for rec in recs:
  u=rec['source'];seen={u};nodes.add(u)
  for edge in rec['answer']['physical_edge_ids']:
   assert 0<=edge<len(dest) and sources[edge]==u;u=dest[edge];assert u not in seen and caps[u]>0;seen.add(u);nodes.add(u)
  assert u==rec['sink']
 return nodes
buckets=defaultdict(lambda:dict(nets=0,baseline_nodes=[0]*4,candidate_nodes=[0]*4,baseline_spans=[0]*4,candidate_spans=[0]*4));ledgers=[Counter(),Counter()];pernet=[]
for net in sorted(inputs[0][0]):
 bs,cs=[data[1][net] for data in inputs];key=(tuple(bs),tuple(cs));bucket=buckets[key];bucket['nets']+=1;counts=[];span_counts=[]
 for arm,data in enumerate(inputs):
  nodes=owned(data[0][net]);ledgers[arm].update(nodes);ns=[0]*4;ss=[0]*4
  for n in nodes:
   if classes[n]>=0:ns[classes[n]]+=1;ss[classes[n]]+=spans[n]
  counts.append(ns);span_counts.append(ss)
  prefix='baseline' if arm==0 else 'candidate'
  bucket[prefix+'_nodes']=[a+b for a,b in zip(bucket[prefix+'_nodes'],ns)];bucket[prefix+'_spans']=[a+b for a,b in zip(bucket[prefix+'_spans'],ss)]
 pernet.append(dict(net_id=net,baseline_status=bs,candidate_status=cs,baseline_nodes=counts[0],candidate_nodes=counts[1],baseline_spans=span_counts[0],candidate_spans=span_counts[1]))
for arm,data in enumerate(inputs):assert dict(ledgers[arm])=={int(k):v for k,v in data[2]['sketch']['ledger'].items()}
rows=[]
for (bs,cs),bucket in sorted(buckets.items()):rows.append(dict(baseline_status=bs,candidate_status=cs,**bucket,node_delta=[b-a for a,b in zip(bucket['baseline_nodes'],bucket['candidate_nodes'])],span_delta=[b-a for a,b in zip(bucket['baseline_spans'],bucket['candidate_spans'])]))
summary=dict(total_NETs=len(pernet),baseline_L16_nodes=sum(x['baseline_nodes'][1]+x['baseline_nodes'][3] for x in pernet),candidate_L16_nodes=sum(x['candidate_nodes'][1]+x['candidate_nodes'][3] for x in pernet),baseline_L16_spans=sum(x['baseline_spans'][1]+x['baseline_spans'][3] for x in pernet),candidate_L16_spans=sum(x['candidate_spans'][1]+x['candidate_spans'][3] for x in pernet))
for condition in ['candidate_any_retained','candidate_last_retained','both_last_committed']:
 selected=[x for x in pernet if ('RETAIN_BUDGET_OR_UNREACHABLE' in x['candidate_status'] if condition=='candidate_any_retained' else x['candidate_status'][1]=='RETAIN_BUDGET_OR_UNREACHABLE' if condition=='candidate_last_retained' else x['candidate_status'][1]==x['baseline_status'][1]=='COMMITTED')]
 summary[condition]=dict(nets=len(selected),L16_node_delta=sum(x['candidate_nodes'][1]+x['candidate_nodes'][3]-x['baseline_nodes'][1]-x['baseline_nodes'][3] for x in selected),L16_span_delta=sum(x['candidate_spans'][1]+x['candidate_spans'][3]-x['baseline_spans'][1]-x['baseline_spans'][3] for x in selected))
assert all(sha(k)==h for k,h in bindings.items());O.mkdir()
(O/'per_NET.json').write_text(json.dumps(pernet)+'\n');bindings[str(O/'per_NET.json')]=sha(O/'per_NET.json')
(O/'attribution.json').write_text(json.dumps(dict(bindings=bindings,full_original_edge_path_and_uniqueNET_ledger_rebuild_pass=True,class_order=['CHANX_L4','CHANX_L16','CHANY_L4','CHANY_L16'],segments=segments,summary=summary,buckets=rows,scope='Full descriptive paired per-NET contribution under changed frozen price objective. Outcome strata are post-treatment, not controlled causal effects; no counterfactual reroute or independent infeasibility certificate for retained attempts. Raw uniqueNET node counts and span totals, not unweighted spatial-bin means or native truth errors.'),indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
