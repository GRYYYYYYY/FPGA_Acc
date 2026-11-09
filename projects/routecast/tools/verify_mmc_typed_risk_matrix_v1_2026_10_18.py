"""Independent graph-spatial reconstruction and new sorted-rank matrix replay."""
import json,sys,math,itertools,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from verify_mmc_pressure_risk_v2_2026_10_18 import rank_info

def main():
 root=R/'experiments/mmc_typed_risk_matrix_v1_2026-10-18';receipt=root/'receipt.json';v=json.loads(receipt.read_text());assert v['status']=='all2160_typed_and_prior_pressure_cells_materialized_independent_metrics_pending'
 prior=R/'experiments/mmc_pressure_risk_matrix_v1_2026-10-18';typed=R/'experiments/mmc_typed_collision_risk_v1_2026-10-18'
 planpath=R/'experiments/mmc_typed_collision_risk_verification_v1_2026-10-18/supplemental_evaluation_protocol_v1.json';plan=json.loads(planpath.read_text())
 bindings={**v['bindings'],str(receipt):sha(receipt),**closure([Path(__file__)])}
 manifest=json.loads((root/'vector_manifest.json').read_text());oldmanifest=json.loads((prior/'vector_manifest.json').read_text());typed_manifest=json.loads((typed/'vector_manifest.json').read_text())
 assert all(manifest[key]==value for key,value in oldmanifest.items())
 domains=json.loads((root/'domains.json').read_text());assert domains==json.loads((prior/'domains.json').read_text()) and domains['byteorder']==sys.byteorder
 inventory=json.loads((typed/'groups.json').read_text());ids={scope:[tuple(key) for key in values] if scope=='spatial' else values for scope,values in domains['ids'].items()};index={n:i for i,n in enumerate(ids['all_positive_RR'])}
 out=R/'experiments/mmc_typed_risk_matrix_verification_v1_2026-10-18';out.mkdir();cache=Cache();summaries=[];new_methods=[family+'__'+source for family in plan['new_families'] for source in plan['source_methods']]
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  config=json.loads((typed/'protocol.json').read_text());ep=json.loads(Path(config['inputs']['case_01']['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==domains['graph_sha256']==inventory['graph_sha256']
  caps=[];kinds=[];members=defaultdict(list);stack=[]
  for event,e in ET.iterparse(graph,events=('start','end')):
   if event=='start':stack.append(e.tag);continue
   if e.tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes':
    n=int(e.get('id'));assert n==len(caps);cap=int(e.get('capacity'));kind=e.get('type');caps.append(cap);kinds.append(kind)
    if cap>0 and kind in ['CHANX','CHANY']:
     loc=e.find('loc');segment=e.find('segment')
     for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
      for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):members[(int(loc.get('layer','0')),x,y,kind,int(segment.get('segment_id')) if segment is not None else -1)].append(n)
    e.clear()
   if e.tag=='rr_nodes':break
   stack.pop()
  assert ids['all_positive_RR']==[n for n,c in enumerate(caps) if c>0]==inventory['positive_RR_ids']
  assert ids['channels']==[n for n,c in enumerate(caps) if c>0 and kinds[n] in ['CHANX','CHANY']] and all(caps[n]==1 for n in ids['channels'])
  assert ids['IPIN']==[n for n,c in enumerate(caps) if c>0 and kinds[n]=='IPIN'] and ids['spatial']==sorted(members)
  assert domains['spatial_capacities']==[sum(caps[n] for n in members[key]) for key in ids['spatial']]
  groups=inventory['groups'];channel_group={n:gid for gid,g in enumerate(groups) if g['kind']=='geometry_channel' for n in g['members']}
  assert set(channel_group)==set(ids['channels'])
  bin_groups={key:Counter(channel_group[n] for n in nodes) for key,nodes in members.items()}
  def read(ref):
   info=manifest[ref];path=Path(info['path']);assert sha(path)==info['sha256'] and path.stat().st_size==info['values']*8
   values=array('d');values.frombytes(path.read_bytes());assert len(values)==info['values'] and all(math.isfinite(x) and x>=0 for x in values);bindings[str(path)]=info['sha256'];return values
  # Reauthenticate all reused vectors, without reranking old admitted cells.
  for info in oldmanifest.values():assert sha(info['path'])==info['sha256'];bindings[info['path']]=info['sha256']
  for case in plan['cases']:
   vectors={};stats={};refs={}
   for source in plan['source_methods']:
    journal=json.loads((typed/(case+'__'+source+'.json')).read_text());active={int(gid):value for gid,value in journal['positive_group_histograms'].items()}
    for family in plan['new_families']:
     method=family+'__'+source;refs[method]={};ref=case+'__'+method+'__all_positive_RR';expected_info=typed_manifest[case+'__'+source+'__'+family]
     assert manifest[ref]==expected_info;full=read(ref);vectors[ref]=full;refs[method]['all_positive_RR']=ref
     for scope in ['channels','IPIN']:
      ref=case+'__'+method+'__'+scope;actual=read(ref);assert actual==array('d',(full[index[n]] for n in ids[scope]));vectors[ref]=actual;refs[method][scope]=ref
     ref=case+'__'+source+'__spatial' if family=='typed_group_mean' else case+'__'+method+'__spatial';actual=read(ref)
     expected=[]
     for key in ids['spatial']:
      if family=='observed_overflow':
       values=[full[index[n]] for n in members[key]];assert all(x.is_integer() for x in values);mass=Fraction(sum(map(int,values)))
      else:
       field='expected_occupancy' if family=='typed_group_mean' else 'expected_overflow'
       mass=sum((Fraction(active[gid][field])*count for gid,count in bin_groups[key].items() if gid in active),Fraction(0))
      expected.append(float(mass/sum(caps[n] for n in members[key])))
     assert actual==array('d',expected);vectors[ref]=actual;refs[method]['spatial']=ref
   oldrows=json.loads((prior/(case+'.json')).read_text())['rows'];rows=json.loads((root/(case+'.json')).read_text())['rows'];assert rows[:288]==oldrows and len(rows)==720
   oldpairs={(row['prediction_vector'],row['truth_vector']):row['metrics'] for row in oldrows};newrows=rows[288:]
   assert {(r['policy'],r['target'],r['domain'],r['method']) for r in newrows}==set(itertools.product(plan['policies'],plan['targets'],plan['domains'],new_methods))
   calculated={};reused=0
   for row in newrows:
    scope=row['domain'];method=row['method'];pred_ref=refs[method][scope];truth_ref=case+'__'+row['policy']+'__'+row['target']+'__'+scope;key=(pred_ref,truth_ref)
    assert row['case']==case and row['prediction_vector']==pred_ref and row['truth_vector']==truth_ref
    if key in oldpairs:assert row['metrics']==oldpairs[key];reused+=1;continue
    if key not in calculated:
     if truth_ref not in vectors:vectors[truth_ref]=read(truth_ref)
     k=20 if scope=='spatial' else max(1,len(ids[scope])//20)
     for ref in key:
      if ref not in stats:stats[ref]=rank_info(vectors[ref],k)
     pa,ta=stats[pred_ref],stats[truth_ref];pred,truth=vectors[pred_ref],vectors[truth_ref];assert len(pred)==len(truth)==len(ids[scope])
     covariance=sum(x*y for x,y in zip(pa['center'],ta['center']));rho=None if pa['variance']==0 or ta['variance']==0 else covariance/math.sqrt(pa['variance']*ta['variance'])
     def interval(fixed,variable,values):
      compulsory=sum(values[i]>variable['boundary'] for i in fixed);eligible=sum(values[i]==variable['boundary'] for i in fixed);slots=k-variable['above']
      return [compulsory+max(0,slots-variable['equal']+eligible),compulsory+min(slots,eligible)]
     hits=len(pa['selected']&ta['selected']);calculated[key]=dict(spearman=rho,k=k,precision_at_k=hits/k,recall_at_k=hits/k,universe_size=len(pred),nonzero_truth=ta['nonzero'],truth_k_boundary=ta['boundary'],prediction_k_boundary=pa['boundary'],top_k_tie_rule='descending value then ascending resource ID',truth_strictly_above=ta['above'],truth_equal_boundary=ta['equal'],prediction_strictly_above=pa['above'],prediction_equal_boundary=pa['equal'],fixed_prediction_truth_tie_hit_interval=interval(pa['selected'],ta,truth),fixed_truth_prediction_tie_hit_interval=interval(ta['selected'],pa,pred))
    expected=calculated[key];actual=row['metrics'];assert actual.keys()==expected.keys()
    for name,value in expected.items():
     if name=='spearman' and value is not None:assert actual[name] is not None and abs(actual[name]-value)<1e-12
     else:assert actual[name]==value,(case,row['policy'],scope,method,name)
   summary=dict(case=case,new_cells_verified=432,new_vector_pairs_reranked=len(calculated),new_cells_transferred_by_exact_old_vector_identity=reused,old_cells_transferred=288,undefined_new_cells=sum(row['metrics']['spearman'] is None for row in newrows))
   assert len(calculated)+reused==432;summaries.append(summary);print(json.dumps(summary),flush=True)
  assert sum(s['new_cells_verified'] for s in summaries)==1296 and all(sha(path)==h for path,h in bindings.items())
  with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,total_cells_verified_or_exactly_transferred=2160,new_cells_verified=1296,prior_cells_transferred=864,scope='Independent originalXML domains and bin memberships, exact rational spatial risks, admitted fullRR vector identities, subset vectors, full sorted integer-rank/overlap/tie checks. Reused cells transfer only by exact inputs and previous proof. Undefined scores retained; no promotion, calibration, cold/heldout/native/full-flow claim.'),stream,indent=2)

if __name__=='__main__':main()
