"""Frozen 1296 new typed-risk cells plus864 unchanged admitted reference cells."""
import json,sys
from pathlib import Path
from array import array
from collections import defaultdict
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from pressure_rank_metrics_v1 import top,metric

def main():
 typed=R/'experiments/mmc_typed_collision_risk_v1_2026-10-18';tp=R/'experiments/mmc_typed_collision_risk_verification_v1_2026-10-18/verification.json';t=json.loads(tp.read_text());assert t['status']=='pass'
 planpath=tp.parent/'supplemental_evaluation_protocol_v1.json';plan=json.loads(planpath.read_text());assert plan['status']=='frozen_before_new_typed_score_outcomes'
 prior=R/'experiments/mmc_pressure_risk_matrix_v1_2026-10-18';pp=R/'experiments/mmc_pressure_risk_verification_v2_2026-10-18/verification.json';p=json.loads(pp.read_text());assert p['status']=='pass'
 bindings={**t['bindings'],**p['bindings'],str(tp):sha(tp),str(pp):sha(pp),str(planpath):sha(planpath),**closure([Path(__file__)])}
 d=R/'experiments/mmc_typed_risk_matrix_v1_2026-10-18';d.mkdir();(d/'vectors').mkdir()
 families=plan['new_families'];sources=plan['source_methods'];newmethods=[family+'__'+source for family in families for source in sources]
 with (d/'protocol.json').open('x') as stream:json.dump(dict(bindings=bindings,frozen_plan=str(planpath),new_methods=newmethods,prior_methods='All12admitted existing density risk methods, copied exactly.',cases=plan['cases'],policies=plan['policies'],targets=plan['targets'],domains=plan['domains'],new_cells=1296,reused_cells=864,total_cells=2160,scope=plan['scope']),stream,indent=2)
 cache=Cache();manifest=json.loads((prior/'vector_manifest.json').read_text());typed_manifest=json.loads((typed/'vector_manifest.json').read_text());summaries=[]
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  domains=json.loads((prior/'domains.json').read_text());ids={scope:[tuple(v) for v in values] if scope=='spatial' else values for scope,values in domains['ids'].items()}
  assert domains['byteorder']==sys.byteorder and domains['array_itemsize']==array('d').itemsize==8
  inventory=json.loads((typed/'groups.json').read_text());assert ids['all_positive_RR']==inventory['positive_RR_ids'] and inventory['graph_sha256']==domains['graph_sha256']
  all_index={n:i for i,n in enumerate(ids['all_positive_RR'])};bin_index={key:i for i,key in enumerate(ids['spatial'])};group_bins={}
  for gid,g in enumerate(inventory['groups']):
   if g['kind']!='geometry_channel':continue
   kind,direction,loc,segment,timing=g['geometry_key'];loc=dict(loc);segment=dict(segment);keys=[]
   for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
    for y in range(int(loc['ylow']),int(loc['yhigh'])+1):keys.append(bin_index[(int(loc.get('layer','0')),x,y,kind,int(segment.get('segment_id','-1')))])
   group_bins[gid]=keys
  def read(info):
   path=Path(info['path']);assert sha(path)==info['sha256'] and path.stat().st_size==info['values']*8
   values=array('d');values.frombytes(path.read_bytes());bindings[str(path)]=info['sha256'];return values
  def save(ref,values):
   path=d/'vectors'/(ref+'.f64')
   with path.open('xb') as stream:values.tofile(stream)
   info=dict(path=str(path),sha256=sha(path),values=len(values));manifest[ref]=info;bindings[str(path)]=info['sha256']
  for case in plan['cases']:
   predictions={};references={};top_cache={}
   for source in sources:
    journal=json.loads((typed/(case+'__'+source+'.json')).read_text());active={int(gid):data for gid,data in journal['positive_group_histograms'].items()}
    for family in families:
     method=family+'__'+source;original_info=typed_manifest[case+'__'+source+'__'+family];full=read(original_info)
     predictions[method]={'all_positive_RR':full};references[method]={}
     ref=case+'__'+method+'__all_positive_RR';manifest[ref]=original_info;references[method]['all_positive_RR']=ref
     for scope in ['channels','IPIN']:
      vector=array('d',(full[all_index[n]] for n in ids[scope]));ref=case+'__'+method+'__'+scope;save(ref,vector);predictions[method][scope]=vector;references[method][scope]=ref
     if family=='typed_group_mean':
      ref=case+'__'+source+'__spatial';vector=read(manifest[ref])
     else:
      totals=[Fraction(0)]*len(ids['spatial'])
      for gid,positions in group_bins.items():
       g=inventory['groups'][gid]
       if family=='observed_overflow':
        loads=[full[all_index[n]] for n in g['members']];assert all(value.is_integer() for value in loads);mass=Fraction(sum(map(int,loads)))
       else:mass=Fraction(active[gid]['expected_overflow'])*len(g['members']) if gid in active else Fraction(0)
       for position in positions:totals[position]+=mass
      vector=array('d',(float(mass/cap) for mass,cap in zip(totals,domains['spatial_capacities'])));ref=case+'__'+method+'__spatial';save(ref,vector)
     predictions[method]['spatial']=vector;references[method]['spatial']=ref
    # Exact group-mean mass proof was independently audited; validate the
    # transferred spatial vector additionally against rational group masses.
    totals=[Fraction(0)]*len(ids['spatial'])
    for gid,positions in group_bins.items():
     mass=Fraction(active[gid]['expected_occupancy'])*len(inventory['groups'][gid]['members']) if gid in active else Fraction(0)
     for position in positions:totals[position]+=mass
    expected=array('d',(float(mass/cap) for mass,cap in zip(totals,domains['spatial_capacities'])))
    assert predictions['typed_group_mean__'+source]['spatial']==expected
   for method,values in predictions.items():
    for scope,vector in values.items():top_cache[references[method][scope]]=top(vector,20 if scope=='spatial' else max(1,len(vector)//20))
   original=json.loads((prior/(case+'.json')).read_text())['rows'];assert len(original)==288;rows=list(original)
   for policy in plan['policies']:
    for target in plan['targets']:
     for scope in plan['domains']:
      truth_ref=case+'__'+policy+'__'+target+'__'+scope;truth=read(manifest[truth_ref]);tt=top(truth,20 if scope=='spatial' else max(1,len(truth)//20))
      for method in newmethods:
       ref=references[method][scope];rows.append(dict(case=case,policy=policy,target=target,domain=scope,method=method,prediction_vector=ref,truth_vector=truth_ref,metrics=metric(predictions[method][scope],truth,top_cache[ref],tt)))
   assert len(rows)==720
   with (d/(case+'.json')).open('x') as stream:json.dump(dict(rows=rows,prior288_cells_transferred_exactly=True,new_cells=432),stream,indent=2)
   view=[dict(policy=row['policy'],method=row['method'],rho=row['metrics']['spearman'],precision_at_k=row['metrics']['precision_at_k']) for row in rows if row['target']=='mean_overflow' and row['domain']=='all_positive_RR' and row['method'] in [family+'__'+plan['primary_reference_source'] for family in families]]
   summary=dict(case=case,reported_cells=720,new_cells=432,undefined_new_cells=sum(row['metrics']['spearman'] is None for row in rows[288:]),primary_reference_full_RR_mean_pressure=view)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(path)==h for path,h in bindings.items())
  with (d/'domains.json').open('x') as stream:json.dump(domains,stream)
  with (d/'vector_manifest.json').open('x') as stream:json.dump(manifest,stream,indent=2)
  bindings.update({str(path):sha(path) for path in d.glob('*.json')})
  with (d/'receipt.json').open('x') as stream:json.dump(dict(status='all2160_typed_and_prior_pressure_cells_materialized_independent_metrics_pending',bindings=bindings,summaries=summaries,total_cells=2160,new_cells=1296,prior_cells_transferred=864,scope='All fixed sources/policies/targets/domains; zero and undefined controls retained. Exact rational spatial collision aggregation, inherited target normalization. No native run, main promotion or calibrated pressure claim.'),stream,indent=2)

if __name__=='__main__':main()
