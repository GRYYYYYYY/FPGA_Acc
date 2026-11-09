"""Evaluate sealed group-density forecasts under unchanged point metrics/gates."""
import json,sys,ast
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from prediction_metrics import compare

def main():
 forecast=R/'experiments/mmc_geometry_pool_forecasts_v1_2026-10-18';receipt=forecast/'receipt.json';r=json.loads(receipt.read_text())
 assert r['status']=='all18_source_only_forecasts_materialized_before_transformed_metrics'
 protocol=forecast/'protocol.json';p=json.loads(protocol.read_text());assert p['primary_candidate']=='pooled_native_retained_on' and p['primary_controls']==['native_retained_on','raw_min_on','previous_native']
 prior=R/'experiments/mmc_terminal_batch_quality_v1_2026-10-18'
 tie_source=R/'tools/evaluate_mmc_old_owner_pressure_quality_case_v1_2026_10_18.py'
 function=next(n for n in ast.parse(tie_source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='ties');namespace={};exec(compile(ast.Module(body=[function],type_ignores=[]),str(tie_source),'exec'),namespace);ties=namespace['ties']
 bindings={**r['bindings'],str(receipt):sha(receipt),str(protocol):sha(protocol),str(tie_source):sha(tie_source),**closure([Path(__file__)])}
 d=R/'experiments/mmc_geometry_pool_quality_v1_2026-10-18';d.mkdir();summaries=[];cache=Cache()
 with (d/'protocol.json').open('x') as stream:json.dump(dict(bindings=bindings,frozen_forecast_protocol=str(protocol),primary_candidate=p['primary_candidate'],primary_controls=p['primary_controls'],scope='Same fixed labels/domains/compare function and exact original ties function.108 new pooled vectors;108 existing vectors transferred from prior independent audits. Spatial conservation must hold exactly; no spatial improvement claimed.'),stream,indent=2)
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  inventory=json.loads((forecast/'groups.json').read_text());groups=inventory['groups'];methods=p['source_methods']
  member_caps={n:cap for g in groups for n,cap in g['members']};assert len(member_caps)==inventory['channels']==258720
  for case in ['case_01','case_02','case_03']:
   f=forecast/(case+'.json');forecast_data=json.loads(f.read_text());assert forecast_data['group_inventory_sha256']==sha(forecast/'groups.json')
   vector_path=prior/case/'vectors.json';original=prior/case/'comparison.json';assert bindings[str(vector_path)]==sha(vector_path) and bindings[str(original)]==sha(original)
   vectors=json.loads(vector_path.read_text());old=json.loads(original.read_text());channels=vectors['channels'];bins=vectors['bins']
   assert {v['node']:v['capacity'] for v in channels}==member_caps
   masses=forecast_data['group_demand_numerators'];concrete={};spatial={m:Counter() for m in methods};bin_caps=Counter()
   for m in methods:concrete[m]={n:masses[m][i]/g['capacity'] for i,g in enumerate(groups) for n,cap in g['members']}
   for i,g in enumerate(groups):
    kind,direction,loc,segment,timing=g['key'];loc=dict(loc);segment=dict(segment)
    assert g['capacity']==sum(cap for n,cap in g['members'])
    for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
     for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
      key=(int(loc.get('layer','0')),x,y,kind,int(segment.get('segment_id','-1')));bin_caps[key]+=g['capacity']
      for m in methods:spatial[m][key]+=masses[m][i]
   assert set(bin_caps)=={tuple(v['key']) for v in bins}
   for v in bins:
    key=tuple(v['key']);assert bin_caps[key]==v['capacity']
    assert all(spatial[m][key]==v['predictions'][m] for m in methods)
   metrics=json.loads(json.dumps(old['metrics']));diagnostics=json.loads(json.dumps(old['tie_diagnostics']))
   for label in old['metrics']:
    tv={v['node']:v['labels'][label]/v['capacity'] for v in channels};tb={tuple(v['key']):v['labels'][label]/v['capacity'] for v in bins}
    for m in methods:
     name='pooled_'+m;pv=concrete[m];pb={key:value/bin_caps[key] for key,value in spatial[m].items()}
     metrics[label][name]=dict(concrete=compare(pv,tv,max(1,len(channels)//20)),spatial=compare(pb,tb,20))
     assert metrics[label][name]['spatial']==metrics[label][m]['spatial']
     diagnostics[label][name]=dict(concrete=ties(pv,tv,max(1,len(channels)//20)),spatial=ties(pb,tb,20))
   checks=[]
   for label in old['metrics']:
    for control in p['primary_controls']:
     comparisons=[]
     for domain in ['concrete','spatial']:
      for metric in ['spearman','precision_at_k']:
       a=metrics[label][p['primary_candidate']][domain][metric];b=metrics[label][control][domain][metric];eps=1e-12 if metric=='spearman' else 0
       comparisons.append(dict(domain=domain,metric=metric,candidate=a,reference=b,nonregression=a is not None and b is not None and a>=b-eps,strict_improvement=a is not None and b is not None and a>b+eps))
     checks.append(dict(label=label,control=control,pass_primary_gate=all(c['nonregression'] for c in comparisons) and any(c['strict_improvement'] for c in comparisons),comparisons=comparisons))
   target=d/(case+'.json')
   with target.open('x') as stream:json.dump(dict(bindings={str(f):sha(f),str(vector_path):sha(vector_path),str(original):sha(original)},metrics=metrics,tie_diagnostics=diagnostics,primary_checks=checks,spatial_mass_and_metrics_exactly_preserved_for_all6sources=True,new_metric_vectors=36,reused_prior_metric_vectors=36,independent_projection_and_metric_audit_pending=True),stream,indent=2)
   bindings[str(target)]=sha(target);summary=dict(case=case,cold_primary_checks=[dict(control=c['control'],pass_primary_gate=c['pass_primary_gate']) for c in checks if c['label']=='cold'],cold_primary_concrete=metrics['cold'][p['primary_candidate']]['concrete'])
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(path)==h for path,h in bindings.items())
  with (d/'receipt.json').open('x') as stream:json.dump(dict(status='all108_pooled_metric_vectors_computed_independent_audit_pending',bindings=bindings,summaries=summaries,new_vectors=108,reused_independently_admitted_vectors=108,scope='Fixed primary pooled endpoint-feedback source, all6 source projections reported, cold main and2fixed supplemental labels. No primary switching or native utility claim.'),stream,indent=2)

if __name__=='__main__':main()
