"""Independent bitset greedy decisions, full-round rebuild and rank metrics."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from prediction_metrics import compare
from verify_wbuart_best_support_ranking_v1 import normalize
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_joint_aggregate_L1_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=D/'verification.json';v=read(source);assert all(sha(p)==h for p,h in v['bindings'].items());graphs={};rows=[];vectors=0;steps=0
 for row in v['rows']:
  ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(x.get('sink_node')) for _,x in ET.iterparse(g) if x.tag=='edge']
  dest=graphs[g];resources=[json.loads(x) for x in Path(row['resources']).read_text().splitlines()];ids=sorted(r['id'] for r in resources);masks={n:1<<i for i,n in enumerate(ids)};pools=defaultdict(list);origins=defaultdict(list);out=Path(row['output']);initial=defaultdict(list);final=defaultdict(list)
  def support(rs):
   mask=0
   for q in rs:
    for edge in q['answer']['physical_edge_ids']:mask|=masks.get(dest[edge],0)
   return mask
  def add(net,rs,origin):
   mask=support(rs)
   if mask not in pools[net]:pools[net].append(mask);origins[net].append(origin)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for net,rs in sorted(initial.items()):add(net,rs,{'stage':'initial'})
  for rnd in read(out/'receipt.json')['rounds']:
   for i,event in enumerate(rnd['events']):
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs,{'round':rnd['round_index'],'event_index':i,'status':event['status']})
  for q in read(out/'round1.json')['records']:final[q['net_id']].append(q)
  selected={net:pools[net].index(support(rs)) for net,rs in final.items()};answer=read(row['diagnostic_payload']);assert answer['label_dependent'] and not answer['admitted_predictor'];assert selected=={int(n):i for n,i in answer['initial_choices'].items()} and {str(n):o for n,o in origins.items()}==answer['pool_origins'];truthcounts={int(n):c for n,c in read(row['truth_payload'])['node_occupancy'].items()};target=[truthcounts.get(n,0) for n in ids]
  def rebuild():
   a=[0]*len(ids)
   for net,choices in pools.items():
    mask=choices[selected[net]]
    while mask:bit=mask&-mask;a[bit.bit_length()-1]+=1;mask-=bit
   return a
  counts=rebuild();score=sum(abs(a-b) for a,b in zip(counts,target));assert score==answer['initial_L1'];cursor=0
  for sweep in range(16):
   changed=0
   for net in sorted(pools):
    oldchoice=selected[net];old=pools[net][oldchoice];best=oldchoice;bestdelta=0
    for j,proposal in enumerate(pools[net]):
     mask=old|proposal;delta=0
     while mask:
      bit=mask&-mask;index=bit.bit_length()-1;value=counts[index]-int(bool(old&bit))+int(bool(proposal&bit));delta+=abs(value-target[index])-abs(counts[index]-target[index]);mask-=bit
     if delta<bestdelta:best,bestdelta=j,delta
    if best==oldchoice:continue
    expected={'sweep':sweep,'net_id':net,'old_choice':oldchoice,'new_choice':best,'delta':bestdelta,'before_L1':score,'after_L1':score+bestdelta};assert answer['moves'][cursor]==expected;cursor+=1;proposal=pools[net][best];mask=old|proposal
    while mask:bit=mask&-mask;counts[bit.bit_length()-1]+=int(bool(proposal&bit))-int(bool(old&bit));mask-=bit
    selected[net]=best;score+=bestdelta;changed+=1
   assert counts==rebuild() and score==sum(abs(a-b) for a,b in zip(counts,target));assert answer['sweeps'][sweep]=={'sweep':sweep,'moves':changed,'L1':score}
   if not changed:break
  assert cursor==len(answer['moves']) and selected=={int(n):i for n,i in answer['selected'].items()};state='ONE_NET_LOCAL_OPTIMUM' if not changed else 'SWEEP_LIMIT_NOT_OPTIMALITY_PROOF';assert answer['status']==state and answer['final_L1']==score;actual={n:c for n,c in zip(ids,counts) if c};assert actual=={int(n):c for n,c in answer['counts'].items()};steps+=cursor;bins=read(Path(row['resources']).parent/'spatial_bins.json');domain=read(row['domain_proof']);truth=normalize(resources,bins,truthcounts);methods={'joint_label_diagnostic':actual,'previous_native':{int(n):c for n,c in read(row['source_frame'])['ledger'].items()},'actual_raw_min':{int(n):c for n,c in read(row['raw_control'])['ledger'].items()}};metrics={}
  for method,value in methods.items():
   value=normalize(resources,bins,value);metrics[method]={};vectors+=1
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    m=compare(value[scope],truth[scope],k);got=row['metrics'][method][scope];assert got['k']==k and got['hits']==round(m['precision_at_k']*k);assert (m['spearman'] is None and got['rho'] is None) or m['spearman'] is not None and abs(m['spearman']-got['rho'])<=1e-12;metrics[method][scope]=got
  checks={}
  for control in ['previous_native','actual_raw_min']:
   nonreg=[];strict=[]
   for scope in ['resource','spatial']:
    a,b=metrics['joint_label_diagnostic'][scope],metrics[control][scope];valid=a['rho'] is not None and b['rho'] is not None;nonreg.extend([valid and a['rho']>=b['rho']-1e-12,a['hits']>=b['hits']]);strict.extend([valid and a['rho']>b['rho']+1e-12,a['hits']>b['hits']])
   checks[control]=all(nonreg) and any(strict)
  assert checks==row['numeric_diagnostic_comparisons'] and all(checks.values())==row['both_numeric_comparisons'];rows.append({key:row[key] for key in ['case','initializer','timing_policy','priority','solver_status','initial_L1','final_L1','moves','both_numeric_comparisons']});print(row['case'],row['initializer'],row['timing_policy'],row['priority'],'JOINT_DIAGNOSTIC_PASS',flush=True)
 assert len(rows)==72 and vectors==216
 files=[source,Path(__file__),R/'tools/verify_wbuart_best_support_ranking_v1.py',R/'tools/prediction_metrics.py',D/'protocol.json'];(D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL72_JOINT_COORDINATE_TRACES_AND216_METRIC_VECTORS_INDEPENDENTLY_VERIFIED','rows':rows,'strict_moves':steps,'metric_vectors':vectors,'bindings':{str(p):sha(p) for p in files},'scope':'Exact greedy decisions/round rebuilds/scores only. Labels used, oneNET local optima are not global optima or joint routing legality; no original prediction admission.'},indent=2)+'\n');print('JOINT_COORDINATE_DIAGNOSTIC_VERIFIED',steps,vectors)
if __name__=='__main__':main()
