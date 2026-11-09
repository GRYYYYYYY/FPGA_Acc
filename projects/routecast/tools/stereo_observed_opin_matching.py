"""Optimistic matching of observed OPIN unions; not full-class reachability."""
import pathlib,json,hashlib,collections
from pin_assignment import assign
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=BASE/'full_pin_ownership_inventory';r=json.loads((src/'receipt.json').read_text());assert sha(src/'owners.json')==r['owners_sha256']
 groups=collections.defaultdict(lambda:collections.defaultdict(set));node_by_key={}
 for row in json.loads((src/'owners.json').read_text()):
  if row['role']!='SOURCE':continue
  key=(row['class_node'],row['ptc']);assert key not in node_by_key;node_by_key[key]=row['pin_node']
  for net in row['net_ids']:groups[row['class_node']][net].add(key)
 assert sum(len(v) for v in groups.values())==61314
 results=[];counts=collections.Counter()
 for cls,candidates in sorted(groups.items()):
  result=assign({n:sorted(pins) for n,pins in candidates.items()});counts[result['status']+'_classes']+=1;counts[result['status']+'_nets']+=len(candidates)
  if result['hall_witness']:
   h=result['hall_witness'];neighbors={p for n in h['request_ids'] for p in candidates[n]}
   assert neighbors=={tuple(p) for p in h['physical_pins']} and len(h['request_ids'])-len(neighbors)==h['deficiency']>0
  results.append({'class_node':cls,'net_count':len(candidates),'candidate_pin_count':len({p for pins in candidates.values() for p in pins}),'result':result})
 out=BASE/'observed_opin_matching';out.mkdir(exist_ok=False);(out/'source').mkdir()
 for name in ['stereo_observed_opin_matching.py','pin_assignment.py']:(out/'source'/name).write_bytes((ROOT/'tools'/name).read_bytes())
 (out/'classes.json').write_text(json.dumps(results)+'\n')
 receipt={'owners_sha256':r['owners_sha256'],'ownership_receipt_sha256':sha(src/'receipt.json'),'classes_sha256':sha(out/'classes.json'),'source_sha256':{p.name:sha(p) for p in (out/'source').iterdir()},'counts':dict(counts),'scope':'optimistic observed OPIN union matching; selecting one pin does not preserve all sink paths; failure only supplied candidates, not full RR classes; excludes reservation constraints'}
 assert sha(src/'owners.json')==r['owners_sha256'];(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(counts))
if __name__=='__main__':main()
