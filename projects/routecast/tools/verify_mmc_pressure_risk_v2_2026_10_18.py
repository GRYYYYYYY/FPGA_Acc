"""Independent XML/vector reconstruction and doubled integer-rank dot products."""
import json,sys,math,itertools,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def rank_info(values,k):
 n=len(values);ordered=sorted(range(n),key=lambda i:(values[i],i));center=array('q',[0])*n;blocks=[];start=0
 while start<n:
  end=start+1
  while end<n and values[ordered[end]]==values[ordered[start]]:end+=1
  rank2=start+end-1-(n-1)
  for j in range(start,end):center[ordered[j]]=rank2
  blocks.append((start,end,values[ordered[start]]));start=end
 selected=set();boundary=None;above=0;equal=0
 for start,end,value in reversed(blocks):
  remaining=k-len(selected);selected.update(ordered[start:start+min(remaining,end-start)])
  if len(selected)==k:boundary=value;above=n-end;equal=end-start;break
 return dict(center=center,variance=sum(v*v for v in center),selected=selected,boundary=boundary,above=above,equal=equal,nonzero=sum(end-start for start,end,value in blocks if value>0))

def main():
 root=R/'experiments/mmc_pressure_risk_matrix_v1_2026-10-18';receipt=root/'receipt.json';r=json.loads(receipt.read_text());assert r['status']=='all864_pressure_risk_cells_computed_independent_replay_pending'
 bindings={**r['bindings'],str(receipt):sha(receipt),**closure([Path(__file__)])}
 manifest=json.loads((root/'vector_manifest.json').read_text());domains=json.loads((root/'domains.json').read_text());assert domains['byteorder']==sys.byteorder and domains['array_type']=='double' and domains['array_itemsize']==array('d').itemsize==8
 forecast=R/'experiments/mmc_geometry_pool_forecasts_v1_2026-10-18';config=json.loads((forecast/'protocol.json').read_text());methods=config['source_methods']
 out=R/'experiments/mmc_pressure_risk_verification_v2_2026-10-18';out.mkdir();cache=Cache();summaries=[];verified_vectors=set()
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  endpoint=json.loads(Path(config['inputs']['case_01']['endpoint']).read_text());graph=Path(endpoint['inputs']['graph']['path']);assert sha(graph)==domains['graph_sha256']
  caps=[];kinds=[];members=defaultdict(list);node_bins={};stack=[]
  for action,e in ET.iterparse(graph,events=('start','end')):
   if action=='start':stack.append(e.tag);continue
   if e.tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes':
    n=int(e.get('id'));assert n==len(caps);cap=int(e.get('capacity'));kind=e.get('type');caps.append(cap);kinds.append(kind)
    if cap>0 and kind in ('CHANX','CHANY'):
     loc=e.find('loc');segment=e.find('segment');keys=[]
     for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
      for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
       key=(int(loc.get('layer','0')),x,y,kind,int(segment.get('segment_id')) if segment is not None else -1);members[key].append(n);keys.append(key)
     node_bins[n]=tuple(keys)
    e.clear()
   if e.tag=='rr_nodes':break
   stack.pop()
  expected_ids=dict(all_positive_RR=[n for n,c in enumerate(caps) if c>0],channels=[n for n,c in enumerate(caps) if c>0 and kinds[n] in ('CHANX','CHANY')],IPIN=[n for n,c in enumerate(caps) if c>0 and kinds[n]=='IPIN'],spatial=sorted(members))
  assert {scope:[tuple(n) for n in ids] if scope=='spatial' else ids for scope,ids in domains['ids'].items()}==expected_ids
  assert domains['spatial_capacities']==[sum(caps[n] for n in members[key]) for key in expected_ids['spatial']]
  groups=json.loads((forecast/'groups.json').read_text())['groups'];group_of={}
  for i,g in enumerate(groups):
   nodes=[n for n,cap in g['members']];assert all(caps[n]==cap for n,cap in g['members']) and g['capacity']==sum(caps[n] for n in nodes)
   assert all(node_bins[n]==node_bins[nodes[0]] for n in nodes)
   for n in nodes:assert n not in group_of;group_of[n]=i
  assert set(group_of)==set(expected_ids['channels'])
  def read(ref):
   info=manifest[ref];path=Path(info['path']);assert sha(path)==info['sha256'] and path.stat().st_size==info['values']*8
   result=array('d');result.frombytes(path.read_bytes());assert len(result)==info['values'] and all(math.isfinite(v) and v>=0 for v in result)
   verified_vectors.add(ref);return result
  for case in ['case_01','case_02','case_03']:
   vectors={};stats={}
   def check(ref,expected):
    actual=read(ref);assert actual==array('d',expected),ref;vectors[ref]=actual
   for method in methods:
    framepath=Path(config['inputs'][case]['predictions'][method]);frame=json.loads(framepath.read_text());ledger={int(n):v for n,v in frame['ledger'].items()}
    if method=='previous_native':
     native_proof=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/independent_xml_verification_v1.json';native=json.loads(native_proof.read_text())
     assert native['all_native_paths_exact'] and native['all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass']
     assert native['bindings'][str(framepath)]==sha(framepath) and native['bindings'][str(graph)]==sha(graph)
     assert bindings[str(native_proof)]==sha(native_proof)
    else:assert frame['graph_sha256']==sha(graph)
    densities=[Fraction(sum(ledger.get(n,0) for n,cap in g['members']),sum(caps[n] for n,cap in g['members'])) for g in groups]
    for scope in ['all_positive_RR','channels','IPIN']:
     check(case+'__'+method+'__'+scope,(float(Fraction(ledger.get(n,0),caps[n])) for n in expected_ids[scope]))
    check(case+'__'+method+'__spatial',(float(Fraction(sum(ledger.get(n,0) for n in members[key]),sum(caps[n] for n in members[key]))) for key in expected_ids['spatial']))
    for scope in ['all_positive_RR','channels']:
     check(case+'__pooled_'+method+'__'+scope,(float(densities[group_of[n]]) if n in group_of else float(Fraction(ledger.get(n,0),caps[n])) for n in expected_ids[scope]))
   pressure=R/'experiments/mmc_checkpoint_pressure_targets_v1_2026-10-18'
   for policy in ['off','on']:
    label=json.loads((pressure/(case+'_'+policy+'.json')).read_text());nt=len(label['checkpoints']);assert label['graph_sha256']==sha(graph) and label['RR_domain_size']==len(caps)
    for target,field in [('mean_overflow','sum_checkpoint_overflow_units'),('peak_overflow','peak_overflow_units'),('overuse_frequency','checkpoints_overused')]:
     numerator={int(n):v for n,v in label[field].items()};assert all(caps[n]>0 for n in numerator)
     for scope in ['all_positive_RR','channels','IPIN']:
      def expected(scope=scope):
       for n in expected_ids[scope]:
        denominator=(nt if target in ['mean_overflow','overuse_frequency'] else 1)*(caps[n] if target in ['mean_overflow','peak_overflow'] else 1)
        yield float(Fraction(numerator.get(n,0),denominator))
      check(case+'__'+policy+'__'+target+'__'+scope,expected())
     check(case+'__'+policy+'__'+target+'__spatial',(float(Fraction(sum(numerator.get(n,0) for n in members[key]),(1 if target=='peak_overflow' else nt)*sum(caps[n] for n in members[key]))) for key in expected_ids['spatial']))
   cells=json.loads((root/(case+'.json')).read_text())['rows'];assert len(cells)==288
   actual_keys={(row['policy'],row['target'],row['domain'],row['method']) for row in cells}
   expected_keys=set(itertools.product(['off','on'],['mean_overflow','peak_overflow','overuse_frequency'],expected_ids,methods+['pooled_'+m for m in methods]));assert actual_keys==expected_keys
   checked={}
   for row in cells:
    scope=row['domain'];method=row['method'];base=method.removeprefix('pooled_') if method.startswith('pooled_') and scope in ['IPIN','spatial'] else method
    pred_ref=case+'__'+base+'__'+scope;truth_ref=case+'__'+row['policy']+'__'+row['target']+'__'+scope
    assert row['prediction_vector']==pred_ref and row['truth_vector']==truth_ref
    k=20 if scope=='spatial' else max(1,len(expected_ids[scope])//20)
    for ref in [pred_ref,truth_ref]:
     if ref not in stats:stats[ref]=rank_info(vectors[ref],k)
    if (pred_ref,truth_ref) not in checked:
     pa,ta=stats[pred_ref],stats[truth_ref];pred,truth=vectors[pred_ref],vectors[truth_ref];n=len(pred);assert n==len(truth)
     cross=sum(a*b for a,b in zip(pa['center'],ta['center']));corr=None if pa['variance']==0 or ta['variance']==0 else cross/math.sqrt(pa['variance']*ta['variance'])
     def bounds(fixed,variable,values):
      compulsory=sum(values[i]>variable['boundary'] for i in fixed);eligible=sum(values[i]==variable['boundary'] for i in fixed);slots=k-variable['above']
      return [compulsory+max(0,slots-(variable['equal']-eligible)),compulsory+min(slots,eligible)]
     value=dict(spearman=corr,k=k,precision_at_k=len(pa['selected']&ta['selected'])/k,recall_at_k=len(pa['selected']&ta['selected'])/k,universe_size=n,nonzero_truth=ta['nonzero'],truth_k_boundary=ta['boundary'],prediction_k_boundary=pa['boundary'],top_k_tie_rule='descending value then ascending resource ID',truth_strictly_above=ta['above'],truth_equal_boundary=ta['equal'],prediction_strictly_above=pa['above'],prediction_equal_boundary=pa['equal'],fixed_prediction_truth_tie_hit_interval=bounds(pa['selected'],ta,truth),fixed_truth_prediction_tie_hit_interval=bounds(ta['selected'],pa,pred))
     checked[(pred_ref,truth_ref)]=value
    expected=checked[(pred_ref,truth_ref)];actual=row['metrics'];assert expected.keys()==actual.keys()
    for name,value in expected.items():
     if name=='spearman' and value is not None:assert actual[name] is not None and abs(value-actual[name])<1e-12
     else:assert actual[name]==value,(case,row['policy'],scope,method,name)
   summary=dict(case=case,all288_reported_cells_independently_checked=True,unique_vector_pairs_ranked=len(checked),unique_vectors_reconstructed=len(vectors),undefined_cells=sum(row['metrics']['spearman'] is None for row in cells))
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert verified_vectors==set(manifest) and all(sha(path)==h for path,h in bindings.items())
  with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,cells_independently_verified=864,unique_vectors_reconstructed=len(verified_vectors),scope='Independent originalXML domains/spans, raw source/group/target vector reconstruction using Fraction normalization, full sorted doubled-integer ranks and topK/tie intervals. Existing exposed partial-seed policies only; no promotion/calibration/cold/heldout/native/full-flow success.'),stream,indent=2)

if __name__=='__main__':main()
