"""Independent complete XML/span projection and histogram metric replay."""
import sys,json,array,math,ast,collections,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';d=E/'mmc_joint_channel_quality_v1_2026-10-18';rp=d/'results.json';r=json.loads(rp.read_text());source=E/'mmc_joint_channel_diamond_v1_2026-10-18';plan=json.loads((E/'mmc_channel_diamond_Pareto_v1_2026-10-18/protocol.json').read_text());ep=json.loads(Path(plan['inputs']['case_01']['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings={**r['bindings'],str(rp):sha(rp),str(graph):sha(graph),str(Path(__file__)):sha(__file__)};data={};totals={};caps=collections.Counter();seen=set()
 for row in r['rows']:
  case=row['case'];prior=E/'mmc_terminal_batch_quality_v1_2026-10-18'/case;proof=json.loads((prior/'verification.json').read_text());vp=prior/'vectors.json';cp=prior/'comparison.json';assert sha(vp)==proof['bindings'][str(vp)] and sha(cp)==proof['bindings'][str(cp)] and proof['bindings'][str(graph)]==ep['graph_sha256'];old=json.loads(vp.read_text());ledger={int(n):v for n,v in json.loads((source/case/'candidate.json').read_text())['ledger'].items()};arrays={}
  for name in ['channels','spatial']:
   p=d/case/(name+'.f64');assert sha(p)==row['files'][str(p)];a=array.array('d');a.frombytes(p.read_bytes());arrays[name]=a;bindings[str(p)]=sha(p)
  data[case]=dict(row=row,old=old,ledger=ledger,arrays=arrays,controls=json.loads(cp.read_text()));totals[case]=collections.Counter()
 stack=[]
 for event,node in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(node);continue
  parent=stack[-2] if len(stack)>1 else None
  if node.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   n=int(node.get('id'));capacity=int(node.get('capacity'));kind=node.get('type')
   if capacity>0 and kind in ['CHANX','CHANY']:
    assert n not in seen;seen.add(n);loc=node.find('loc');seg=node.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
    for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
     for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
      key=(int(loc.get('layer','0')),x,y,kind,sid);caps[key]+=capacity
      for case,v in data.items():totals[case][key]+=v['ledger'].get(n,0)
   parent.remove(node);node.clear()
  if node.tag=='rr_nodes':break
  stack.pop()
 helper=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';fn=next(n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric');ns=dict(Counter=collections.Counter,math=math,checked=0);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(helper),'exec'),ns);bindings[str(helper)]=sha(helper);summaries=[]
 for case,v in data.items():
  old=v['old'];channels=old['channels'];bins=old['bins'];assert {x['node'] for x in channels}==seen and len(channels)==len(seen)==258720;assert {tuple(b['key']) for b in bins}==set(caps) and len(bins)==17160
  cv=v['arrays']['channels'];bv=v['arrays']['spatial'];assert len(cv)==len(channels) and len(bv)==len(bins)
  for i,x in enumerate(channels):assert cv[i]==v['ledger'].get(x['node'],0)/x['capacity']
  for i,x in enumerate(bins):key=tuple(x['key']);assert x['capacity']==caps[key] and bv[i]==totals[case][key]/caps[key]
  row=v['row'];checks=[]
  for label in channels[0]['labels']:
   for domain,table,values,k in [('concrete',channels,cv,len(channels)//20),('spatial',bins,bv,20)]:
    ids=[x['node'] for x in table] if domain=='concrete' else [tuple(x['key']) for x in table];pred=dict(zip(ids,values));truth={i:x['labels'][label]/x['capacity'] for i,x in zip(ids,table)};ns['audit_metric'](pred,truth,row['metrics'][label][domain],k)
   for control in ['native_retained_on','raw_min_on','previous_native']:
    comparisons=[]
    for domain in ['concrete','spatial']:
     for metric in ['spearman','precision_at_k']:
      a=row['metrics'][label][domain][metric];b=v['controls']['metrics'][label][control][domain][metric];eps=1e-12 if metric=='spearman' else 0;comparisons.append(dict(domain=domain,metric=metric,candidate=a,control=b,nonregression=a is not None and b is not None and a>=b-eps,strict_improvement=a is not None and b is not None and a>b+eps))
    checks.append(dict(label=label,control=control,comparisons=comparisons,passed=all(x['nonregression'] for x in comparisons) and any(x['strict_improvement'] for x in comparisons)))
  assert checks==row['checks'];cold=[x for x in checks if x['label']=='cold' and x['control'] in ['raw_min_on','previous_native']];assert row['original_cold_gate']==all(x['passed'] for x in cold);assert row['extended_three_control_all_label_gate']==all(x['passed'] for x in checks);summaries.append(dict(case=case,cold_gate=row['original_cold_gate'],cold_metrics=row['metrics']['cold'],failed_cold_controls=[x['control'] for x in cold if not x['passed']]))
 assert ns['checked']==18
 for p,h in bindings.items():assert sha(p)==h
 result=dict(status='all_three_joint_candidate_complete_domains_and18metric_vectors_verified',bindings=bindings,rows=summaries,decision='All3original cold gates remain failed. Do not promote this diamond selector as a final-congestion predictor or start a native utility trial from the0.0026percent source-objective reduction alone. Retain exact path/objective support result, close this selected-candidate branch without weight/label-driven retries. No unseen/native/net-time/hardware claim.')
 with (d/'verification_and_decision_v1.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(summaries,indent=2),flush=True)
if __name__=='__main__':main()
