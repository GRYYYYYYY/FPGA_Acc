"""Frozen full MMC channel/span quality cross-matrix on common native labels."""
import json,sys,time,re,math,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
from audit_native_route import NODE
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[1]);start=time.perf_counter();P=json.loads((D/'protocol.json').read_text());bindings={**closure([Path(__file__)]),str(D/'protocol.json'):sha(D/'protocol.json')}
assert all(sha(p)==h for p,h in P['bindings'].items());bindings.update(P['bindings']);assert sha(P['frozen_cohort_protocol'])==P['frozen_cohort_protocol_sha256'];assert P['primary_candidate']=='all_NET_on' and P['primary_controls']==['raw_min_on','previous_native']
def load(path):
 path=Path(path);bindings[str(path)]=sha(path);return json.loads(path.read_text())
def admit(path,flag):
 v=load(path);assert v[flag] and all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);return v
cohort=admit(R/P['native_admission'],'all_native_physical_and_canonical_pass')
model=Path(P['model_directory'])
owner_audit=admit(P['all_NET_audit'],'all3_full_frames_and_all_NET_event_replays_pass')
case=Path(P['endpoint']).parents[1].name
for kind in ['frame','events']:
 proofpath=Path(P['all_NET_audit']).parent/f'{case}_{kind}.json';proof=load(proofpath);assert owner_audit['bindings'][str(proofpath)]==sha(proofpath);assert all(sha(k)==h for k,h in proof['bindings'].items());bindings.update(proof['bindings'])
assert bindings[str(Path(P['predictions']['all_NET_on']))]==sha(P['predictions']['all_NET_on'])
supplemental=admit(P['owner_frame_audit'],'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass')
assert supplemental['bindings'][str(Path(P['predictions']['owner_expansion_on']))]==sha(P['predictions']['owner_expansion_on'])
admit(model/'initial_independent_verification_v1.json','all115572V2budgets_matched')
admit(model/'feedback_audits/verification.json','both_final_and_all_event_audits_pass')
admit(model/'fresh_raw/independent_xml_verification_v2.json','all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass')
admit(R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/independent_xml_verification_v1.json','all_native_paths_exact')
ep_path=Path(P['endpoint']);ep=load(ep_path);wanted={ep['net_names'][str(q['net_id'])] for q in ep['connections']};graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=sha(graph)
routes={'cold':Path(P['native_admission']).parent/'cold/output.route'}
HEADER=re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)(.*)$')
def printed_occupancy(route):
 unions=defaultdict(set);current=None
 with Path(route).open() as f:
  for line in f:
   header=HEADER.match(line)
   if header:current=header[2] if not header[3].strip() else None;continue
   match=NODE.match(line)
   if match:
    if current is None or current not in wanted:raise ValueError('unmapped physical route NET')
    unions[current].add(int(match[1]))
   elif line.lstrip().startswith('Node:'):raise ValueError('unparsed printed node')
 assert set(unions)==wanted
 return Counter(n for nodes in unions.values() for n in nodes)
labels={}
for arm,path in P['labels'].items():
 route=routes[arm];assert cohort['bindings'][str(route)]==sha(route);bindings[str(route)]=sha(route);v=load(R/path)
 assert v['all_printed_branch_arc_switch_and_union_checks_pass'] and v['overflow_units']==0
 assert v['inputs_sha256']['graph']==ep['graph_sha256'] and v['inputs_sha256']['route']==sha(route)
 actual=printed_occupancy(route);assert dict(actual)=={int(n):v for n,v in v['node_occupancy'].items()};labels[arm]=actual
print('ALL LABELS authenticated and full printed NET unions matched',flush=True)
predictions={};frame_info={}
for method,path in P['predictions'].items():
 frame=load(R/path);assert frame['required_connections']==frame['completed_connections']==115572
 predictions[method]={int(n):v for n,v in frame['ledger'].items()};frame_info[method]={k:frame.get(k) for k in ['overflow_units','eligible_for_legal_route_commit','scope']}
oldgeo=load(R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json');oldroute=Path(oldgeo['previous_native_route']);assert bindings.get(str(oldroute))==sha(oldroute);assert predictions['previous_native']==dict(printed_occupancy(oldroute))
channels=[];bins={};stack=[];seen=set();counts=Counter()
for event,node in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(node);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if node.tag=='node' and parent=='rr_nodes':
  nid=int(node.get('id'));kind=node.get('type');capacity=int(node.get('capacity'));counts[kind]+=1
  if kind in {'CHANX','CHANY'} and capacity>0:
   assert nid not in seen;seen.add(nid);pr={m:d.get(nid,0) for m,d in predictions.items()};tr={m:d.get(nid,0) for m,d in labels.items()};assert all(type(v) is int and v>=0 for v in [*pr.values(),*tr.values()]);assert all(v<=capacity for v in tr.values())
   channels.append(dict(node=nid,capacity=capacity,predictions=pr,labels=tr));loc=node.find('loc');segment=node.find('segment');sid=int(segment.get('segment_id')) if segment is not None else -1
   for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
    for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
     key=(int(loc.get('layer','0')),x,y,kind,sid)
     if key not in bins:bins[key]=dict(key=key,capacity=0,predictions={m:0 for m in predictions},labels={m:0 for m in labels})
     b=bins[key];b['capacity']+=capacity
     for m,v in pr.items():b['predictions'][m]+=v
     for m,v in tr.items():b['labels'][m]+=v
  stack[-2].remove(node);node.clear()
 if node.tag=='rr_nodes':break
 stack.pop()
bin_rows=[bins[k] for k in sorted(bins)];assert channels and bin_rows
print('DOMAIN',len(channels),'channels',len(bin_rows),'bins',flush=True)
with (D/'vectors.json').open('x') as f:json.dump(dict(channels=channels,bins=bin_rows),f);f.write('\n')
def ties(pred,truth,k):
 ids=sorted(truth);k=min(k,len(ids));ps=sorted(ids,key=lambda i:(-pred[i],i))[:k];ts=sorted(ids,key=lambda i:(-truth[i],i))[:k];bound=truth[ts[-1]];above={i for i in ids if truth[i]>bound};equal={i for i in ids if truth[i]==bound};fixed=set(ps);base=len(fixed&above);choices=k-len(above);within=len(fixed&equal);pb=pred[ps[-1]]
 return dict(truth_strictly_above=len(above),truth_equal_boundary=len(equal),truth_slots_from_tie=choices,prediction_strictly_above=sum(v>pb for v in pred.values()),prediction_equal_boundary=sum(v==pb for v in pred.values()),fixed_prediction_truth_tie_min_hits=base+max(0,choices-(len(equal)-within)),fixed_prediction_truth_tie_max_hits=base+min(choices,within))
metrics={};ties_result={}
for label in labels:
 metrics[label]={};ties_result[label]={}
 for method in predictions:
  metrics[label][method]={};ties_result[label][method]={}
  for scope,data,key,k in [('concrete',channels,'node',max(1,len(channels)//20)),('spatial',bin_rows,'key',20)]:
   def identity(x):return tuple(x[key]) if key=='key' else x[key]
   pv={identity(x):x['predictions'][method]/x['capacity'] for x in data};tv={identity(x):x['labels'][label]/x['capacity'] for x in data}
   metrics[label][method][scope]=compare(pv,tv,k);ties_result[label][method][scope]=ties(pv,tv,k)
checks=[]
for label in labels:
 for control in P['primary_controls']:
  comparisons=[]
  for scope in ['concrete','spatial']:
   for metric in ['spearman','precision_at_k']:
    baseline=metrics[label][control][scope][metric];candidate=metrics[label][P['primary_candidate']][scope][metric];eps=1e-12 if metric=='spearman' else 0
    comparisons.append(dict(scope=scope,metric=metric,reference=baseline,candidate=candidate,nonregression=baseline is not None and candidate is not None and candidate>=baseline-eps,strict_improvement=baseline is not None and candidate is not None and candidate>baseline+eps))
  checks.append(dict(label=label,control=control,comparisons=comparisons,pass_primary_gate=all(x['nonregression'] for x in comparisons) and any(x['strict_improvement'] for x in comparisons)))
assert all(sha(p)==h for p,h in bindings.items());bindings[str(D/'vectors.json')]=sha(D/'vectors.json')
result=dict(bindings=bindings,metrics=metrics,tie_diagnostics=ties_result,primary_checks=checks,primary_gate_pass=all(x['pass_primary_gate'] for x in checks),complete_positive_channel_universe=len(channels),complete_span_bin_universe=len(bins),all_labels_from_bound_accepted_routes_and_full_printed_unions=True,prediction_frame_info=frame_info,independent_metric_and_domain_audit_pending=True,heldout_family=False,seconds=time.perf_counter()-start,scope=P['evidence_scope'])
with (D/'comparison.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(primary_gate_pass=result['primary_gate_pass'],primary_checks=checks)),flush=True)
