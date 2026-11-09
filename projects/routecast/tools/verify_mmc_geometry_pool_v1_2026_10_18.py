"""Independent XML grouping/source mass/rank/tie and original gate audit."""
import json,sys,ast,math,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 froot=R/'experiments/mmc_geometry_pool_forecasts_v1_2026-10-18';quality=R/'experiments/mmc_geometry_pool_quality_v1_2026-10-18'
 proof=quality/'receipt.json';receipt=json.loads(proof.read_text());assert receipt['status']=='all108_pooled_metric_vectors_computed_independent_audit_pending'
 p=json.loads((froot/'protocol.json').read_text());inventory=json.loads((froot/'groups.json').read_text());groups=inventory['groups'];methods=p['source_methods']
 audit_source=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py'
 fn=next(n for n in ast.parse(audit_source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric');ns=dict(Counter=Counter,math=math,checked=0);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(audit_source),'exec'),ns)
 bindings={**receipt['bindings'],str(proof):sha(proof),str(audit_source):sha(audit_source),**closure([Path(__file__)])}
 out=R/'experiments/mmc_geometry_pool_verification_v1_2026-10-18';out.mkdir();cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  endpoint=json.loads(Path(p['inputs']['case_01']['endpoint']).read_text());graph=Path(endpoint['inputs']['graph']['path'])
  assert inventory['graph_sha256']==sha(graph)
  # Key encoding differs from producer tuple keys; grouping is read afresh.
  meta={};stack=[]
  def signature(kind,direction,loc,segment,timing):
   return json.dumps(dict(kind=kind,direction=direction,geometry=loc,segment=segment,timing=timing),sort_keys=True,separators=(',',':'))
  for event,node in ET.iterparse(graph,events=('start','end')):
   if event=='start':stack.append(node.tag);continue
   if node.tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes':
    cap=int(node.get('capacity'))
    if cap>0 and node.get('type') in ['CHANX','CHANY']:
     loc=dict(node.find('loc').attrib);loc={k:value for k,value in loc.items() if k!='ptc'};loc['layer']=loc.get('layer','0')
     seg=node.find('segment');timing=node.find('timing')
     key=signature(node.get('type'),node.get('direction'),loc,dict(seg.attrib) if seg is not None else {},dict(timing.attrib) if timing is not None else {})
     n=int(node.get('id'));assert n not in meta;meta[n]=(key,cap)
    node.clear()
   if node.tag=='rr_nodes':break
   stack.pop()
  seen=set();keys=set();geometry=[]
  for g in groups:
   ids=[n for n,cap in g['members']];assert len(ids)==len(set(ids)) and seen.isdisjoint(ids);seen.update(ids)
   actual={meta[n][0] for n in ids};assert len(actual)==1
   key=next(iter(actual));assert key not in keys;keys.add(key)
   assert all(meta[n][1]==cap for n,cap in g['members']) and g['capacity']==sum(meta[n][1] for n in ids)
   kind,direction,loc,segment,timing=g['key'];assert signature(kind,direction,dict(loc),dict(segment),dict(timing))==key
   geometry.append(json.loads(key))
  assert seen==set(meta) and len(seen)==inventory['channels']==258720 and len(groups)==29832
  prior=R/'experiments/mmc_terminal_batch_quality_v1_2026-10-18'
  for case in ['case_01','case_02','case_03']:
   projected=json.loads((froot/(case+'.json')).read_text());result=json.loads((quality/(case+'.json')).read_text())
   vectors=json.loads((prior/case/'vectors.json').read_text());baseline=json.loads((prior/case/'comparison.json').read_text())
   assert {v['node']:v['capacity'] for v in vectors['channels']}=={n:cap for n,(key,cap) in meta.items()}
   concrete={};spatial={m:Counter() for m in methods};bin_caps=Counter();masses={}
   for m in methods:
    path=Path(p['inputs'][case]['predictions'][m]);assert sha(path)==projected['source_hashes'][m]
    ledger={int(n):value for n,value in json.loads(path.read_text())['ledger'].items()}
    assert all(v['predictions'][m]==ledger.get(v['node'],0) for v in vectors['channels'])
    values=[sum(ledger.get(n,0) for n,cap in g['members']) for g in groups]
    assert values==projected['group_demand_numerators'][m];masses[m]=values
    concrete[m]={n:float(Fraction(values[i],g['capacity'])) for i,g in enumerate(groups) for n,cap in g['members']}
    assert all(Fraction(values[i],g['capacity'])*sum(cap for n,cap in g['members'])==values[i] for i,g in enumerate(groups))
   for i,g in enumerate(groups):
    actual=geometry[i];loc=actual['geometry'];segment=actual['segment']
    for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
     for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
      key=(int(loc['layer']),x,y,actual['kind'],int(segment.get('segment_id','-1')));bin_caps[key]+=g['capacity']
      for m in methods:spatial[m][key]+=masses[m][i]
   assert set(bin_caps)=={tuple(v['key']) for v in vectors['bins']}
   for b in vectors['bins']:
    key=tuple(b['key']);assert b['capacity']==bin_caps[key] and all(b['predictions'][m]==spatial[m][key] for m in methods)
   for label in ['cold','partial_seed_default','partial_seed_firstpass_preserve']:
    tv={v['node']:v['labels'][label]/v['capacity'] for v in vectors['channels']};tb={tuple(v['key']):v['labels'][label]/v['capacity'] for v in vectors['bins']}
    for m in methods:
     assert result['metrics'][label][m]==baseline['metrics'][label][m]
     name='pooled_'+m
     assert result['metrics'][label][name]['spatial']==baseline['metrics'][label][m]['spatial']
     for domain,pred,truth,k in [('concrete',concrete[m],tv,len(meta)//20),('spatial',{key:spatial[m][key]/cap for key,cap in bin_caps.items()},tb,20)]:
      metric=result['metrics'][label][name][domain];ns['audit_metric'](pred,truth,metric,k)
      ids=sorted(truth);pred_top=set(sorted(ids,key=lambda n:(-pred[n],n))[:k]);truth_top=sorted(ids,key=lambda n:(-truth[n],n))[:k]
      cut=truth[truth_top[-1]];above={n for n in ids if truth[n]>cut};equal={n for n in ids if truth[n]==cut};slots=k-len(above);base=len(pred_top&above);inside=len(pred_top&equal)
      diag=result['tie_diagnostics'][label][name][domain];pboundary=metric['prediction_k_boundary']
      assert diag==dict(truth_strictly_above=len(above),truth_equal_boundary=len(equal),truth_slots_from_tie=slots,prediction_strictly_above=sum(v>pboundary for v in pred.values()),prediction_equal_boundary=sum(v==pboundary for v in pred.values()),fixed_prediction_truth_tie_min_hits=base+max(0,slots-len(equal-pred_top)),fixed_prediction_truth_tie_max_hits=base+min(slots,inside))
   checks=[]
   for label in ['cold','partial_seed_default','partial_seed_firstpass_preserve']:
    for control in p['primary_controls']:
     fields=[]
     for domain in ['concrete','spatial']:
      for metric in ['spearman','precision_at_k']:
       value=result['metrics'][label][p['primary_candidate']][domain][metric];reference=result['metrics'][label][control][domain][metric];eps=1e-12 if metric=='spearman' else 0
       fields.append(dict(domain=domain,metric=metric,candidate=value,reference=reference,nonregression=value is not None and reference is not None and value>=reference-eps,strict_improvement=value is not None and reference is not None and value>reference+eps))
     checks.append(dict(label=label,control=control,pass_primary_gate=all(f['nonregression'] for f in fields) and any(f['strict_improvement'] for f in fields),comparisons=fields))
   assert checks==result['primary_checks']
   summary=dict(case=case,new_metric_vectors_checked=36,source_and_group_mass_exact=True,all6_spatial_vectors_and_metrics_unchanged=True,cold_primary_checks=[dict(control=c['control'],pass_primary_gate=c['pass_primary_gate']) for c in checks if c['label']=='cold'])
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert ns['checked']==108 and all(sha(path)==h for path,h in bindings.items())
  with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,positive_channels=258720,groups=29832,new_metric_vectors_independently_verified=108,prior_metric_vectors_transferred=108,all3_cold_primary_gates_pass=all(c['pass_primary_gate'] for s in summaries for c in s['cold_primary_checks']),scope='Independent originalXML partition, exact source/group/spatial mass and histogram rank/topK/MAE/tie/gate validation. Geometry grouping is a forecast prior, not functional equivalence or a legal route. Exposed cases only; no new native/full-flow claim.'),stream,indent=2)

if __name__=='__main__':main()
