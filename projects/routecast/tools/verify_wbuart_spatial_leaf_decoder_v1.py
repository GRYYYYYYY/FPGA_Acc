"""Independent real replay: no calls into production solver or traversal."""
import json
from array import array
from fractions import Fraction as F
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_spatial_leaf_decoder_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 frozen=D/'predictions_frozen.json';v=read(frozen);assert len(v['rows'])==9 and not v['heldout_labels_used_for_fit'];assert all(sha(p)==h for p,h in v['bindings'].items())
 features={r['case']:r for r in read(E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json')['rows']};specs={r['case']:r['specification'] for r in read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons']};results=[]
 for fold in v['folds']:
  dec=read(fold['decoder']);model=read(dec['original_model']);train=model['training_cases'];test=model['test_cases'];assert len(train)==6 and len(test)==3 and not set(train)&set(test);states={i:int(2*n['positive']>=n['rows']) for i,n in enumerate(model['nodes']) if n['feature']==-1};rows=[];capacities=[];assign={}
  for case in train+test:
   f=features[case];a=array('d');a.frombytes(Path(f['matrix']).read_bytes());ids=read(f['resource_ids']);assert len(a)==len(ids)*41
   assigned=[]
   for j in range(len(ids)):
    current=0
    while model['nodes'][current]['feature']!=-1:
     node=model['nodes'][current];current=node['right'] if a[j*41+node['feature']]>node['threshold'] else node['left']
    assigned.append(current)
   assign[case]=assigned
   if case not in train:continue
   spec=read(specs[case]);truth={int(k):value for k,value in read(spec['label_physical_audit'])['node_occupancy'].items()};resources={x['id']:x for x in map(json.loads,Path(f['resources']).read_text().splitlines())};bins=read(Path(f['resources']).parent/'spatial_bins.json');offset=len(capacities);lookup={tuple(x['key']):offset+j for j,x in enumerate(bins)};capacities.extend(x['capacity'] for x in bins)
   rows.extend((owner,truth.get(rid,0),[lookup[tuple(key)] for key in resources[rid]['bins']]) for rid,owner in zip(ids,assigned))
  assert len(rows)==model['training_rows']
  # Rebuild per-leaf tables independently from all rows, then each proposal's
  # full aggregate from all leaf tables. No incremental residual/delta formula.
  tables={k:[0,0,{}] for k in states};targets=[0]*len(capacities)
  for owner,y,bins in rows:
   t=tables[owner];t[0]+=1;t[1]+=y
   for j in bins:t[2][j]=t[2].get(j,0)+1;targets[j]+=y
  for k,(n,p,_) in tables.items():assert n==model['nodes'][k]['rows'] and p==model['nodes'][k]['positive']
  def energy(s):
   counts=[0]*len(capacities);errors=0
   for k,(n,p,incidence) in tables.items():
    errors+=n-p if s[k] else p
    if s[k]:
     for j,count in incidence.items():counts[j]+=count
   return F(errors,len(rows))+sum((F((x-y)**2,len(capacities)*c*c) for x,y,c in zip(counts,targets,capacities)),F(0))
  current=energy(states);assert current==F(dec['initial_energy'],dec['denominator']);index=0
  for sweep in range(16):
   flips=0
   for k in sorted(states):
    proposed={**states,k:1-states[k]};value=energy(proposed);t=dec['trace'][index];assert t['sweep']==sweep and t['leaf']==k and F(t['before'],dec['denominator'])==current and F(t['delta'],dec['denominator'])==value-current and t['accepted']==(value<current)
    if value<current:states=proposed;current=value;flips+=1
    index+=1
   if not flips:break
  assert index==len(dec['trace']) and states=={int(k):val for k,val in dec['states'].items()} and current==F(dec['final_energy'],dec['denominator']) and dec['converged']==(flips==0) and dec['sweeps']==sweep+1
  count=0
  for case in test:
   r=next(r for r in v['rows'] if r['case']==case);assert r['decoder']==fold['decoder'];actual=read(r['point_counts']);assert actual==[states[k] for k in assign[case]];count+=len(actual)
  results.append({'episode':fold['episode'],'decisions':index,'heldout_points':count,'initial_loss':float(F(dec['initial_energy'],dec['denominator'])),'final_loss':float(current),'flips':sum(t['accepted'] for t in dec['trace'])});print('INDEPENDENT_REAL_REPLAY_PASS',results[-1],flush=True)
 out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'PASS_ALL3_REAL_TRACES_AND9_HELDOUT_FIELDS','folds':results,'bindings':{str(p):sha(p) for p in [frozen,Path(__file__)]},'scope':'Train-only replay; no quality admission.'},indent=2)+'\n')
if __name__=='__main__':main()
