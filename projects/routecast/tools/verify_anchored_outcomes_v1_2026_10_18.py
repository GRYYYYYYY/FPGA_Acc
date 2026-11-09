"""Independent XML spatial domains, sorted integer ranks and original cold gates."""
import hashlib,itertools,json,math,xml.etree.ElementTree as ET
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from verify_mmc_pressure_risk_v2_2026_10_18 import rank_info

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def assert_metrics(actual,expected):
 assert actual.keys()==expected.keys()
 for k,value in expected.items():
  if k in ['spearman','mae'] and value is not None:assert actual[k] is not None and abs(actual[k]-value)<1e-12,(k,actual[k],value)
  else:assert actual[k]==value,(k,actual[k],value)
def calc(pred,truth,k,pa,ta):
 cross=sum(a*b for a,b in zip(pa['center'],ta['center']));rho=None if not pa['variance'] or not ta['variance'] else cross/math.sqrt(pa['variance']*ta['variance']);hits=len(pa['selected']&ta['selected'])
 def interval(fixed,var,values):
  forced=sum(values[i]>var['boundary'] for i in fixed);eligible=sum(values[i]==var['boundary'] for i in fixed);slots=k-var['above']
  return [forced+max(0,slots-var['equal']+eligible),forced+min(slots,eligible)]
 return dict(spearman=rho,k=k,precision_at_k=hits/k,recall_at_k=hits/k,universe_size=len(pred),nonzero_truth=ta['nonzero'],truth_k_boundary=ta['boundary'],prediction_k_boundary=pa['boundary'],top_k_tie_rule='descending value then ascending resource ID',truth_strictly_above=ta['above'],truth_equal_boundary=ta['equal'],prediction_strictly_above=pa['above'],prediction_equal_boundary=pa['equal'],fixed_prediction_truth_tie_hit_interval=interval(pa['selected'],ta,truth),fixed_truth_prediction_tie_hit_interval=interval(ta['selected'],pa,pred))

def main():
 out=Path('experiments/mmc_anchored_outcomes_verification_v1_2026-10-18');out.mkdir(exist_ok=False)
 root=Path('experiments/mmc_anchored_pressure_matrix_v1_2026-10-18');source=Path('experiments/mmc_anchored_NET_forecasts_v1_2026-10-18');prior=Path('experiments/mmc_typed_risk_matrix_v1_2026-10-18');verification=Path('experiments/mmc_anchored_NET_forecasts_verification_v1_2026-10-18');planpath=verification/'frozen_outcome_protocol_v1.json';plan=json.loads(planpath.read_text());pres=plan['pressure'];methods=[f+'__'+s for f in plan['families'] for s in plan['sources']]
 receipt=root/'receipt.json';r=json.loads(receipt.read_text());assert r['status']=='all3024_pressure_cells_materialized_independent_metrics_pending'
 coldpath=Path('experiments/mmc_anchored_cold_quality_v1_2026-10-18/results.json');cold=json.loads(coldpath.read_text());assert cold['status']=='all36_cold_rows_computed_independent_metrics_pending'
 oldproofpath=Path('experiments/mmc_typed_risk_matrix_verification_v1_2026-10-18/verification.json');oldproof=json.loads(oldproofpath.read_text());assert oldproof['status']=='pass'
 bindings={**r['bindings'],**cold['bindings'],str(receipt.resolve()):sha(receipt),str(coldpath.resolve()):sha(coldpath),str(planpath.resolve()):sha(planpath),str(Path(__file__).resolve()):sha(__file__),str(Path('tools/verify_mmc_pressure_risk_v2_2026_10_18.py').resolve()):sha('tools/verify_mmc_pressure_risk_v2_2026_10_18.py')}
 for p,h in bindings.items():assert sha(p)==h
 domains=json.loads((root/'domains.json').read_text());assert domains==json.loads((prior/'domains.json').read_text());ids=domains['ids'];idx={n:i for i,n in enumerate(ids['all_positive_RR'])};manifest=json.loads((root/'vector_manifest.json').read_text());oldmanifest=json.loads((prior/'vector_manifest.json').read_text());newmanifest=json.loads((source/'vector_manifest.json').read_text());assert all(manifest[k]==v for k,v in oldmanifest.items())
 for name,info in oldmanifest.items():assert sha(info['path'])==info['sha256']==oldproof['bindings'][info['path']]
 gp=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json');inventory=json.loads(gp.read_text());groups=inventory['groups'];group_of={n:gid for gid,g in enumerate(groups) if g['kind']=='geometry_channel' for n in g['members']};config=json.loads(Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/protocol.json').read_text());endpoint=json.loads(Path(config['inputs']['case_01']['endpoint']).read_text());graph=Path(endpoint['inputs']['graph']['path']);assert sha(graph)==inventory['graph_sha256']==domains['graph_sha256']
 members=defaultdict(list);caps={};kinds={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e.tag);continue
  if e.tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes':
   n=int(e.get('id'));cap=int(e.get('capacity'));kind=e.get('type');caps[n]=cap;kinds[n]=kind
   if cap>0 and kind in ['CHANX','CHANY']:
    loc=e.find('loc');seg=e.find('segment')
    for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
     for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):members[(int(loc.get('layer','0')),x,y,kind,int(seg.get('segment_id')) if seg is not None else -1)].append(n)
   e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert ids['all_positive_RR']==[n for n,c in caps.items() if c>0];assert ids['channels']==[n for n,c in caps.items() if c>0 and kinds[n] in ['CHANX','CHANY']];assert ids['IPIN']==[n for n,c in caps.items() if c>0 and kinds[n]=='IPIN'];assert ids['spatial']==[list(k) for k in sorted(members)];assert domains['spatial_capacities']==[sum(caps[n] for n in members[k]) for k in sorted(members)]
 bin_groups={key:Counter(group_of[n] for n in ns) for key,ns in members.items()}
 for key,counts in bin_groups.items():assert all(count==len(groups[gid]['members']) for gid,count in counts.items())
 def read(info):
  assert sha(info['path'])==info['sha256'];a=array('d');a.frombytes(Path(info['path']).read_bytes());assert len(a)==info['values'] and all(math.isfinite(x) and x>=0 for x in a);bindings[info['path']]=info['sha256'];return a
 summaries=[];cold_verified=0
 for case in plan['cases']:
  vectors={};stats={};refs={}
  for source_name in plan['sources']:
   journal=json.loads((source/(case+'__'+source_name+'.json')).read_text())['group_totals']
   for family in plan['families']:
    method=family+'__'+source_name;refs[method]={};ref=case+'__'+method+'__all_positive_RR';assert manifest[ref]==newmanifest[case+'__'+source_name+'__'+family];full=read(manifest[ref]);vectors[ref]=full;refs[method]['all_positive_RR']=ref
    for scope in ['channels','IPIN']:
     ref=case+'__'+method+'__'+scope;values=read(manifest[ref]);assert values==array('d',(full[idx[n]] for n in ids[scope]));vectors[ref]=values;refs[method][scope]=ref
    ref=case+'__'+source_name+'__spatial' if family=='anchored_group_mean' else case+'__'+method+'__spatial';values=read(manifest[ref]);field='expected_occupancy_total' if family=='anchored_group_mean' else 'expected_overflow_total';expected=[]
    for key in sorted(members):
     mass=sum((Fraction(journal[str(gid)][field]) for gid in bin_groups[key] if str(gid) in journal),Fraction(0));expected.append(float(mass/sum(caps[n] for n in members[key])))
    assert values==array('d',expected);vectors[ref]=values;refs[method]['spatial']=ref
  oldcase=prior/(case+'.json');assert sha(oldcase)==oldproof['bindings'][str(oldcase.resolve())];oldrows=json.loads(oldcase.read_text())['rows'];casepath=root/(case+'.json');rows=json.loads(casepath.read_text())['rows'];bindings[str(casepath.resolve())]=sha(casepath);assert len(rows)==1008 and rows[:720]==oldrows
  newrows=rows[720:];assert {(x['policy'],x['target'],x['domain'],x['method']) for x in newrows}==set(itertools.product(pres['policies'],pres['targets'],pres['domains'],methods))
  for row in newrows:
   scope=row['domain'];pref=refs[row['method']][scope];tref=case+'__'+row['policy']+'__'+row['target']+'__'+scope;assert row['prediction_vector']==pref and row['truth_vector']==tref and row['case']==case
   if tref not in vectors:vectors[tref]=read(manifest[tref])
   k=20 if scope=='spatial' else max(1,len(ids[scope])//20)
   for ref in [pref,tref]:
    if ref not in stats:stats[ref]=rank_info(vectors[ref],k)
   assert_metrics(row['metrics'],calc(vectors[pref],vectors[tref],k,stats[pref],stats[tref]))
  base=Path('experiments/mmc_multiplacement_quality_v1_2026-10-18')/case;data=json.loads((base/'vectors.json').read_text());old=json.loads((base/'comparison.json').read_text())['metrics']['cold'];crows=[x for x in cold['rows'] if x['case']==case];assert len(crows)==12
  assert {(x['source'],x['domain']) for x in crows}==set(itertools.product(plan['sources'],plan['cold']['domains']))
  for row in crows:
   scope='channels' if row['domain']=='concrete' else 'spatial';pref=refs[row['method']][scope];pred=vectors[pref];items=data['channels'] if scope=='channels' else data['bins'];truth=array('d',(x['labels']['cold']/x['capacity'] for x in items));k=20 if scope=='spatial' else max(1,len(pred)//20);pa=rank_info(pred,k);ta=rank_info(truth,k);allmetrics=calc(pred,truth,k,pa,ta);expected={key:allmetrics[key] for key in row['metrics'] if key!='mae'};expected['mae']=sum(abs(a-b) for a,b in zip(pred,truth))/len(pred);assert_metrics(row['metrics'],expected);cold_verified+=1
   if scope=='spatial' and row['source'] in old:assert row['metrics']==old[row['source']]['spatial']
  ccase=next(x for x in cold['cases'] if x['case']==case);candidate={x['domain']:x['metrics'] for x in crows if x['method']==plan['cold']['primary']};passed=[]
  for check in ccase['primary_checks']:
   comparisons=[]
   for domain in ['concrete','spatial']:
    for metric_name in ['spearman','precision_at_k']:
     a,b=candidate[domain][metric_name],old[check['control']][domain][metric_name];eps=1e-12 if metric_name=='spearman' else 0;comparisons.append(dict(domain=domain,metric=metric_name,candidate=a,reference=b,nonregression=a is not None and b is not None and a>=b-eps,strict_improvement=a is not None and b is not None and a>b+eps))
   assert check['comparisons']==comparisons;assert check['pass_gate']==(all(x['nonregression'] for x in comparisons) and any(x['strict_improvement'] for x in comparisons))
   if check['original_primary_control']:passed.append(check['pass_gate'])
  assert ccase['original_primary_gate_pass']==all(passed)
  summary=dict(case=case,new_pressure_cells_verified=288,old_pressure_cells_transferred=720,cold_rows_verified=12,cold_original_gate_pass=ccase['original_primary_gate_pass']);summaries.append(summary);print('ANCHORED OUTCOME REPLAY PASS',json.dumps(summary),flush=True)
 assert cold_verified==36
 for path,h in bindings.items():assert sha(path)==h
 for path in [root/'vector_manifest.json',root/'domains.json']:
  bindings[str(path.resolve())]=sha(path)
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,pressure_new_cells_verified=864,pressure_old_cells_transferred=2160,cold_rows_verified=36,scope='Independent originalXML spatial membership/capacities and exact rational group-total aggregation, full sorted integer rank/topK/tie/MAE replay and unchanged cold gates. Development only; no calibrated pressure, strict unseen, native utility or full-flow promotion.'),f,indent=2)
if __name__=='__main__':main()
