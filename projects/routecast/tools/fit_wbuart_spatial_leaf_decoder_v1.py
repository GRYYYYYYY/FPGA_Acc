"""Train-only leaf states; freeze all heldout fields before quality evaluation."""
import json
from array import array
from pathlib import Path
from spatial_leaf_decoder_v1 import solve
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
def read(p): return json.loads(Path(p).read_text())
def leaf(row, model):
 i=0
 while model['nodes'][i]['feature']>=0:
  n=model['nodes'][i]; i=n['left'] if row[n['feature']]<=n['threshold'] else n['right']
 return i

def main():
 D=E/'wbuart_spatial_leaf_decoder_v1_2026-10-20'; D.mkdir(exist_ok=False)
 fp=E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json'
 features={r['case']:r for r in read(fp)['rows']}
 wp=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json'
 specs={r['case']:r['specification'] for r in read(wp)['comparisons']}
 bindings={}; outputs=[]; folds=[]
 def bind(p): bindings[str(p)]=sha(p)
 for p in [Path(__file__),R/'tools/spatial_leaf_decoder_v1.py',fp,wp,E/'spatial_leaf_decoder_contract_v1_2026-10-20/verification.json',E/'wbuart_spatial_leaf_decoder_design_v1_2026-10-20/protocol.json']:bind(p)
 for episode in ['episode_01','episode_02','episode_03']:
  mp=E/'wbuart_paired_bbox_cart_v1_2026-10-20'/episode/'main/model.json'; model=read(mp);bind(mp)
  initial={i:int(2*(n['positive']+1)>=n['rows']+2) for i,n in enumerate(model['nodes']) if n['feature']<0}
  leaves=[];truth=[];memberships=[];capacities=[];assignments={}
  for case in model['training_cases']+model['test_cases']:
   f=features[case];a=array('d');a.frombytes(Path(f['matrix']).read_bytes());assert len(a)==f['rows']*41
   assignments[case]=[leaf(a[i*41:(i+1)*41],model) for i in range(f['rows'])]
   bind(f['matrix']);bind(f['resource_ids'])
   if case not in model['training_cases']:continue
   spec=read(specs[case]);bind(specs[case]);tp=spec['label_physical_audit'];target={int(k):v for k,v in read(tp)['node_occupancy'].items()};bind(tp)
   resources={r['id']:r for r in map(json.loads,Path(f['resources']).read_text().splitlines())}
   bp=Path(f['resources']).parent/'spatial_bins.json'; bins=read(bp);bind(bp);bind(f['resources'])
   offset=len(capacities);index={tuple(b['key']):offset+j for j,b in enumerate(bins)};capacities.extend(b['capacity'] for b in bins)
   ids=read(f['resource_ids']);leaves.extend(assignments[case]);truth.extend(target.get(i,0) for i in ids)
   memberships.extend([index[tuple(key)] for key in resources[i]['bins']] for i in ids)
  result=solve(leaves,truth,memberships,capacities,initial)
  assert len(truth)==model['training_rows'] and all(y in (0,1) for y in truth)
  out=D/episode;out.mkdir();dp=out/'decoder.json';dp.write_text(json.dumps({'original_model':str(mp),'training_cases':model['training_cases'],'test_cases':model['test_cases'],**result},indent=2)+'\n');bind(dp)
  for case in model['test_cases']:
   p=out/(case.replace('/','_')+'_point_counts.json');p.write_text(json.dumps([result['states'][v] for v in assignments[case]])+'\n');bind(p)
   outputs.append({'case':case,'mode':'main','decoder':str(dp),'model':str(mp),'resource_ids':features[case]['resource_ids'],'point_counts':str(p)})
  folds.append({'episode':episode,'decoder':str(dp),'converged':result['converged'],'sweeps':result['sweeps'],'flips':sum(t['accepted'] for t in result['trace']),'initial_energy':result['initial_energy'],'final_energy':result['final_energy'],'denominator':result['denominator']})
  print('LEAF_DECODER_FROZEN',episode,folds[-1],flush=True)
 (D/'predictions_frozen.json').write_text(json.dumps({'status':'ALL9_TRAIN_ONLY_LEAF_DECODER_FIELDS_FROZEN_PENDING_INDEPENDENT_REPLAY','rows':outputs,'folds':folds,'bindings':bindings,'heldout_labels_used_for_fit':False,'scope':'Retrospective exposed WBUART; no quality or native routing admission.'},indent=2)+'\n')
if __name__=='__main__':main()
