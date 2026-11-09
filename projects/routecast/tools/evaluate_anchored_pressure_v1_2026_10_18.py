"""Frozen anchored-pressure matrix, preserving all2160 admitted reference cells."""
import hashlib,json
from array import array
from fractions import Fraction
from pathlib import Path
from pressure_rank_metrics_v1 import top,metric

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/mmc_anchored_pressure_matrix_v1_2026-10-18');out.mkdir(exist_ok=False);(out/'vectors').mkdir()
 source=Path('experiments/mmc_anchored_NET_forecasts_v1_2026-10-18');verification=Path('experiments/mmc_anchored_NET_forecasts_verification_v1_2026-10-18');vp=verification/'verification.json';v=json.loads(vp.read_text());assert v['status']=='pass'
 planpath=verification/'frozen_outcome_protocol_v1.json';plan=json.loads(planpath.read_text());pressure=plan['pressure'];prior=Path('experiments/mmc_typed_risk_matrix_v1_2026-10-18');oldproof=Path('experiments/mmc_typed_risk_matrix_verification_v1_2026-10-18/verification.json');op=json.loads(oldproof.read_text());assert op['status']=='pass'
 bindings={**v['bindings'],str(vp.resolve()):sha(vp),str(planpath.resolve()):sha(planpath),str(oldproof.resolve()):sha(oldproof),str(Path(__file__).resolve()):sha(__file__),str(Path('tools/pressure_rank_metrics_v1.py').resolve()):sha('tools/pressure_rank_metrics_v1.py')}
 for p,h in bindings.items():assert sha(p)==h
 domains=json.loads((prior/'domains.json').read_text());ids=domains['ids'];index={n:i for i,n in enumerate(ids['all_positive_RR'])};bins={tuple(key):i for i,key in enumerate(ids['spatial'])}
 gp=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json');g=json.loads(gp.read_text());assert ids['all_positive_RR']==g['positive_RR_ids'];groupbins={}
 for gid,group in enumerate(g['groups']):
  if group['kind']!='geometry_channel':continue
  kind,direction,loc,segment,timing=group['geometry_key'];loc=dict(loc);segment=dict(segment)
  groupbins[gid]=[bins[(int(loc.get('layer','0')),x,y,kind,int(segment.get('segment_id','-1')))] for x in range(int(loc['xlow']),int(loc['xhigh'])+1) for y in range(int(loc['ylow']),int(loc['yhigh'])+1)]
 manifest=json.loads((prior/'vector_manifest.json').read_text());source_manifest=json.loads((source/'vector_manifest.json').read_text());newmethods=[f+'__'+s for f in plan['families'] for s in plan['sources']]
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,frozen_plan=str(planpath.resolve()),new_methods=newmethods,old_cells=2160,new_cells=864,scope=plan['scope']),f,indent=2)
 def read(info):
  assert sha(info['path'])==info['sha256'];a=array('d');a.frombytes(Path(info['path']).read_bytes());assert len(a)==info['values'];return a
 def save(ref,values):
  path=out/'vectors'/(ref+'.f64')
  with path.open('xb') as f:values.tofile(f)
  manifest[ref]=dict(path=str(path.resolve()),sha256=sha(path),values=len(values));return ref
 for case in plan['cases']:
  refs={};vectors={};tops={}
  for source_name in plan['sources']:
   journal=json.loads((source/(case+'__'+source_name+'.json')).read_text())['group_totals']
   for family in plan['families']:
    method=family+'__'+source_name;refs[method]={};info=source_manifest[case+'__'+source_name+'__'+family];full=read(info);ref=case+'__'+method+'__all_positive_RR';manifest[ref]=info;refs[method]['all_positive_RR']=ref;vectors[ref]=full
    for scope in ['channels','IPIN']:
     ref=case+'__'+method+'__'+scope;values=array('d',(full[index[n]] for n in ids[scope]));save(ref,values);refs[method][scope]=ref;vectors[ref]=values
    if family=='anchored_group_mean':
     ref=case+'__'+source_name+'__spatial';values=read(manifest[ref])
    else:
     totals=[Fraction(0)]*len(bins)
     for gid,positions in groupbins.items():
      mass=Fraction(journal[str(gid)]['expected_overflow_total']) if str(gid) in journal else Fraction(0)
      for position in positions:totals[position]+=mass
     values=array('d',(float(m/c) for m,c in zip(totals,domains['spatial_capacities'])));ref=case+'__'+method+'__spatial';save(ref,values)
    refs[method]['spatial']=ref;vectors[ref]=values
  for ref,values in vectors.items():tops[ref]=top(values,20 if ref.endswith('__spatial') else max(1,len(values)//20))
  oldrows=json.loads((prior/(case+'.json')).read_text())['rows'];assert len(oldrows)==720;rows=list(oldrows)
  for policy in pressure['policies']:
   for target in pressure['targets']:
    for scope in pressure['domains']:
     truthref=case+'__'+policy+'__'+target+'__'+scope;truth=read(manifest[truthref]);tt=top(truth,20 if scope=='spatial' else max(1,len(truth)//20))
     for method in newmethods:
      ref=refs[method][scope];rows.append(dict(case=case,policy=policy,target=target,domain=scope,method=method,prediction_vector=ref,truth_vector=truthref,metrics=metric(vectors[ref],truth,tops[ref],tt)))
  assert len(rows)==1008
  with (out/(case+'.json')).open('x') as f:json.dump(dict(rows=rows),f,indent=2)
  print('ANCHORED PRESSURE CELLS DONE',case,len(rows),flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'domains.json').open('x') as f:json.dump(domains,f)
 with (out/'vector_manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='all3024_pressure_cells_materialized_independent_metrics_pending',bindings=bindings,new_cells=864,old_cells=2160,scope=plan['scope']),f,indent=2)
if __name__=='__main__':main()
