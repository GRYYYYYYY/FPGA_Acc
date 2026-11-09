"""Frozen exposed-only pressure risk matrix, with replayable compact vectors."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from pressure_rank_metrics_v1 import top,metric

def main():
 planpath=R/'experiments/routecast_validation_semantics_v1_2026-10-18/prospective_validation_requirements_v1.json';plan=json.loads(planpath.read_text())
 assert plan['status']=='requirements_and_exposed_supplemental_evaluation_frozen_before_pressure_scores'
 pressure=R/'experiments/mmc_checkpoint_pressure_targets_v1_2026-10-18';pp=pressure/'independent_verification_v1.json';p=json.loads(pp.read_text());assert p['status']=='pass'
 forecast=R/'experiments/mmc_geometry_pool_forecasts_v1_2026-10-18';fp=R/'experiments/mmc_geometry_pool_verification_v1_2026-10-18/verification.json';f=json.loads(fp.read_text());assert f['status']=='pass'
 core=R/'experiments/pressure_rank_metrics_core_v1_2026-10-18/verification.json';c=json.loads(core.read_text());assert c['status']=='pass'
 bindings={**p['bindings'],**f['bindings'],**c['bindings'],**closure([Path(__file__)])}
 for path in [planpath,pp,fp,core,forecast/'protocol.json']:bindings[str(path)]=sha(path)
 config=json.loads((forecast/'protocol.json').read_text());methods=plan['exposed_pressure_evaluation']['source_methods'];assert methods==config['source_methods']
 d=R/'experiments/mmc_pressure_risk_matrix_v1_2026-10-18';d.mkdir();(d/'vectors').mkdir()
 with (d/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,frozen_plan=str(planpath),methods=methods+['pooled_'+m for m in methods],targets=['mean_overflow','peak_overflow','overuse_frequency'],domains=['all_positive_RR','channels','IPIN','spatial'],target_normalization='Mean=sum_overflow/(checkpoints*RRcap), peak=peak_overflow/RRcap, frequency=overused_checkpoints/checkpoints. Spatial aggregates channel numerators over identical original span bins; mean/frequency divide by checkpoints*bin_capacity; peak by bin_capacity. Spatial peak is sum of perRR sampled peaks, not maximum simultaneous bin pressure.',metric_backend='Histogram average-rank correlation and cached exact topK; original full-sort parity certified by200random vectors plus tie subset oracles.',expected_reported_cells=864,scope='Descriptive uncalibrated risk ranking on6already-exposed partial-seed traces, not cold labels, new generalization or a replacement primary gate. No MAE/calibration success claim.'),stream,indent=2)
 cache=Cache();manifest={};results=[]
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  ep=json.loads(Path(config['inputs']['case_01']['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);caps=array('Q');types=[];stack=[]
  for event,node in ET.iterparse(graph,events=('start','end')):
   if event=='start':stack.append(node);continue
   if node.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
    assert int(node.get('id'))==len(caps);caps.append(int(node.get('capacity')));types.append(node.get('type'));stack[-2].remove(node);node.clear()
   if node.tag=='rr_nodes':break
   stack.pop()
  inventory=json.loads((forecast/'groups.json').read_text());groups=inventory['groups'];assert inventory['graph_sha256']==sha(graph)
  ids={name:[n for n,cap in enumerate(caps) if cap>0 and (name=='all_positive_RR' or name=='channels' and types[n] in ['CHANX','CHANY'] or name=='IPIN' and types[n]=='IPIN')] for name in ['all_positive_RR','channels','IPIN']}
  assert len(ids['channels'])==258720 and all(caps[n]==1 for n in ids['channels'])
  group_of={n:i for i,g in enumerate(groups) for n,cap in g['members']};bin_caps=Counter();group_bins=[]
  for g in groups:
   kind,direction,loc,segment,timing=g['key'];loc=dict(loc);segment=dict(segment);keys=[]
   for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
    for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
     key=(int(loc.get('layer','0')),x,y,kind,int(segment.get('segment_id','-1')));keys.append(key);bin_caps[key]+=g['capacity']
   group_bins.append(keys)
  ids['spatial']=sorted(bin_caps);assert len(ids['spatial'])==17160
  with (d/'domains.json').open('x') as stream:json.dump(dict(graph_sha256=sha(graph),ids=ids,spatial_capacities=[bin_caps[key] for key in ids['spatial']],byteorder=sys.byteorder,array_type='double',array_itemsize=array('d').itemsize),stream)
  def save(name,values):
   path=d/'vectors'/(name+'.f64')
   with path.open('xb') as stream:values.tofile(stream)
   manifest[name]=dict(path=str(path),sha256=sha(path),values=len(values));return name
  for case in ['case_01','case_02','case_03']:
   predictions={};pred_refs={};forecast_case=json.loads((forecast/(case+'.json')).read_text());all_index={n:i for i,n in enumerate(ids['all_positive_RR'])}
   for m in methods:
    path=Path(config['inputs'][case]['predictions'][m]);assert sha(path)==forecast_case['source_hashes'][m]
    ledger={int(n):v for n,v in json.loads(path.read_text())['ledger'].items()}
    raw={scope:array('d',(ledger.get(n,0)/caps[n] for n in ids[scope])) for scope in ['all_positive_RR','channels','IPIN']}
    spatial=Counter()
    for i,g in enumerate(groups):
     mass=sum(ledger.get(n,0) for n,cap in g['members'])
     assert mass==forecast_case['group_demand_numerators'][m][i]
     for key in group_bins[i]:spatial[key]+=mass
    raw['spatial']=array('d',(spatial[key]/bin_caps[key] for key in ids['spatial']))
    pooled=dict(raw);pooled_all=array('d',raw['all_positive_RR'])
    for i,g in enumerate(groups):
     density=forecast_case['group_demand_numerators'][m][i]/g['capacity']
     for n,cap in g['members']:pooled_all[all_index[n]]=density
    pooled['all_positive_RR']=pooled_all;pooled['channels']=array('d',(pooled_all[all_index[n]] for n in ids['channels']))
    for method,values in [(m,raw),('pooled_'+m,pooled)]:
     predictions[method]=values;pred_refs[method]={}
     for scope,vector in values.items():
      if method.startswith('pooled_') and scope in ['IPIN','spatial']:pred_refs[method][scope]=pred_refs[m][scope]
      else:pred_refs[method][scope]=save(case+'__'+method+'__'+scope,vector)
   pred_tops={}
   for method,values in predictions.items():
    for scope,vector in values.items():
     key=pred_refs[method][scope]
     if key not in pred_tops:pred_tops[key]=top(vector,20 if scope=='spatial' else max(1,len(vector)//20))
   case_rows=[]
   for policy in ['off','on']:
    targetpath=pressure/(case+'_'+policy+'.json');assert bindings[str(targetpath)]==sha(targetpath);label=json.loads(targetpath.read_text());nt=len(label['checkpoints'])
    assert label['graph_sha256']==sha(graph) and label['RR_domain_size']==len(caps)
    for target,field in [('mean_overflow','sum_checkpoint_overflow_units'),('peak_overflow','peak_overflow_units'),('overuse_frequency','checkpoints_overused')]:
     numerators={int(n):v for n,v in label[field].items()};values={}
     for scope in ['all_positive_RR','channels','IPIN']:
      values[scope]=array('d',(numerators.get(n,0)/((nt if target!='peak_overflow' else 1)*(1 if target=='overuse_frequency' else caps[n])) for n in ids[scope]))
     spatial=Counter()
     for n,value in numerators.items():
      if n in group_of:
       for key in group_bins[group_of[n]]:spatial[key]+=value
     values['spatial']=array('d',(spatial[key]/((nt if target!='peak_overflow' else 1)*bin_caps[key]) for key in ids['spatial']))
     cell_cache={}
     for scope,truth in values.items():
      truth_ref=save(case+'__'+policy+'__'+target+'__'+scope,truth);tt=top(truth,20 if scope=='spatial' else max(1,len(truth)//20))
      for method,pred in predictions.items():
       ref=pred_refs[method][scope]
       if ref not in cell_cache:cell_cache[ref]=metric(pred[scope],truth,pred_tops[ref],tt)
       row=dict(case=case,policy=policy,target=target,domain=scope,method=method,prediction_vector=ref,truth_vector=truth_ref,metrics=cell_cache[ref])
       case_rows.append(row)
   assert len(case_rows)==288
   with (d/(case+'.json')).open('x') as stream:json.dump(dict(rows=case_rows,all12_methods_all2policies_all3targets_all4domains=True),stream,indent=2)
   results.extend(case_rows);print('PRESSURE RISK MATRIX CASE COMPLETE',case,'cells',len(case_rows),flush=True)
  assert len(results)==864 and all(sha(path)==h for path,h in bindings.items())
  with (d/'vector_manifest.json').open('x') as stream:json.dump(manifest,stream,indent=2)
  bindings.update({str(path):sha(path) for path in d.glob('*.json')})
  with (d/'receipt.json').open('x') as stream:json.dump(dict(status='all864_pressure_risk_cells_computed_independent_replay_pending',bindings=bindings,cells=864,unique_binary_vectors=len(manifest),scope='All fixed sources, policies, targets and complete domains reported. Identical pooled IPIN/spatial vectors explicitly share source files. No promotion gate, calibration, cold/unseen validation, native run or full-flow gain.'),stream,indent=2)

if __name__=='__main__':main()
