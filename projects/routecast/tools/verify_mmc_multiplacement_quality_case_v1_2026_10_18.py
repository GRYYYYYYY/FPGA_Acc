"""Independent printed-node, full XML-domain and histogram-metric validation."""
import ast,json,math,sys,time,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[1]);tick=time.perf_counter();rp=D/'comparison.json';r=json.loads(rp.read_text());P=json.loads((D/'protocol.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)}
vectors=json.loads((D/'vectors.json').read_text());channels={x['node']:x for x in vectors['channels']};bins={tuple(x['key']):x for x in vectors['bins']};assert len(channels)==len(vectors['channels']) and len(bins)==len(vectors['bins'])
pred={m:{int(n):v for n,v in json.loads((R/p).read_text())['ledger'].items()} for m,p in P['predictions'].items()};truth={}
routes={'cold':Path(P['native_admission']).parent/'cold/output.route'}
for label,path in P['labels'].items():
 proof=json.loads((R/path).read_text());route=routes[label];assert proof['inputs_sha256']['route']==sha(route)==bindings[str(route)]
 # Independent token lexer with numeric NET IDs, not producer name/regex parser.
 unions={};current=None;printed=0
 with route.open() as stream:
  for line in stream:
   words=line.split()
   if words and words[0]=='Net':
    current=int(words[1]) if line.rstrip().endswith(')') else None
    if current is not None:
     assert current not in unions;unions[current]=set()
   elif words and words[0]=='Node:':
    assert current is not None;unions[current].add(int(words[1]));printed+=1
 counts=Counter(n for nodes in unions.values() for n in nodes);assert dict(counts)=={int(n):v for n,v in proof['node_occupancy'].items()};assert printed==proof['printed_nodes'];assert sum(bool(nodes) for nodes in unions.values())==proof['routed_nets']==55300;truth[label]=counts
seen=set();caps=Counter();pb={m:Counter() for m in pred};tb={m:Counter() for m in truth};ep=json.loads(Path(P['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);stack=[]
for event,node in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(node);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if node.tag=='node' and parent=='rr_nodes':
  n=int(node.get('id'));capacity=int(node.get('capacity'));kind=node.get('type')
  if capacity>0 and kind in ('CHANX','CHANY'):
   assert n in channels and n not in seen;seen.add(n);c=channels[n];assert c['capacity']==capacity and c['predictions']=={m:d.get(n,0) for m,d in pred.items()} and c['labels']=={m:d.get(n,0) for m,d in truth.items()}
   loc=node.find('loc');segment=node.find('segment');seg=int(segment.get('segment_id')) if segment is not None else -1
   positions=((int(loc.get('layer','0')),x,y,kind,seg) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1))
   for key in positions:
    caps[key]+=capacity
    for m in pred:pb[m][key]+=pred[m].get(n,0)
    for m in truth:tb[m][key]+=truth[m].get(n,0)
  stack[-2].remove(node);node.clear()
 if node.tag=='rr_nodes':break
 stack.pop()
assert seen==set(channels) and set(caps)==set(bins)
for key,b in bins.items():assert b['capacity']==caps[key] and b['predictions']=={m:pb[m][key] for m in pred} and b['labels']=={m:tb[m][key] for m in truth}
print('INDEPENDENT full printed labels and XML/span domain PASS',len(channels),len(bins),flush=True)
audit_source=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';bindings[str(audit_source)]=sha(audit_source);fn=next(n for n in ast.parse(audit_source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric');ns=dict(Counter=Counter,math=math,checked=0);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(audit_source),'exec'),ns)
for label in truth:
 for method in pred:
  for scope,data,key,k in [('concrete',vectors['channels'],'node',max(1,len(channels)//20)),('spatial',vectors['bins'],'key',20)]:
   identity=lambda x:tuple(x[key]) if key=='key' else x[key]
   pv={identity(x):x['predictions'][method]/x['capacity'] for x in data};tv={identity(x):x['labels'][label]/x['capacity'] for x in data};metric=r['metrics'][label][method][scope];ns['audit_metric'](pv,tv,metric,k)
   ids=sorted(tv);top_pred=set(sorted(ids,key=lambda i:(-pv[i],i))[:k]);top_truth=sorted(ids,key=lambda i:(-tv[i],i))[:k];cut=tv[top_truth[-1]];strict={i for i in ids if tv[i]>cut};tie={i for i in ids if tv[i]==cut};choose=k-len(strict);base=len(top_pred&strict);available=len(top_pred&tie);diag=r['tie_diagnostics'][label][method][scope]
   pboundary=r['metrics'][label][method][scope]['prediction_k_boundary'];assert diag['prediction_strictly_above']==sum(x>pboundary for x in pv.values()) and diag['prediction_equal_boundary']==sum(x==pboundary for x in pv.values())
   assert diag['truth_strictly_above']==len(strict) and diag['truth_equal_boundary']==len(tie) and diag['truth_slots_from_tie']==choose
   assert diag['fixed_prediction_truth_tie_min_hits']==base+max(0,choose-len(tie-top_pred)) and diag['fixed_prediction_truth_tie_max_hits']==base+min(choose,available)
derived=[]
for label in truth:
 for control in P['primary_controls']:
  comparisons=[]
  for scope in ['concrete','spatial']:
   for name in ['spearman','precision_at_k']:
    baseline=r['metrics'][label][control][scope][name];candidate=r['metrics'][label][P['primary_candidate']][scope][name];eps=1e-12 if name=='spearman' else 0
    comparisons.append(dict(scope=scope,metric=name,reference=baseline,candidate=candidate,nonregression=baseline is not None and candidate is not None and candidate>=baseline-eps,strict_improvement=baseline is not None and candidate is not None and candidate>baseline+eps))
  derived.append(dict(label=label,control=control,comparisons=comparisons,pass_primary_gate=all(x['nonregression'] for x in comparisons) and any(x['strict_improvement'] for x in comparisons)))
assert derived==r['primary_checks'] and r['primary_gate_pass']==all(x['pass_primary_gate'] for x in derived)
assert ns['checked']==10
assert all(sha(p)==h for p,h in bindings.items())
result=dict(status='pass',bindings=bindings,complete_original_XML_positive_channel_and_span_domains_equal=True,all_native_labels_independently_token_replayed=True,full_prediction_and_label_vectors_equal_source_ledgers=True,histogram_rank_topk_mae_checks=ns['checked'],truth_tie_interval_checks=10,source_protocol_frozen_before_computation=True,primary_gate_pass=r['primary_gate_pass'],heldout_family=False,seconds=time.perf_counter()-tick,scope='Independent domain, printed native union and numerical metric validation. One additional frozen exposed placement with a cold native label; no generalization, causal placement improvement or full workflow gain.')
with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2)
print('PASS independent MMC common-label matrix',ns['checked'],'metric vectors',flush=True)
