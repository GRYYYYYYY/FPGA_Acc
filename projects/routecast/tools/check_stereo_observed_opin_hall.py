"""Independent certificate check: Hall deficit rules out disjoint nonempty sets."""
import pathlib,json,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 inv=BASE/'full_pin_ownership_inventory';match=BASE/'observed_opin_matching';r=json.loads((match/'receipt.json').read_text());ir=json.loads((inv/'receipt.json').read_text())
 assert sha(inv/'owners.json')==r['owners_sha256']==ir['owners_sha256'];assert sha(inv/'receipt.json')==r['ownership_receipt_sha256'];assert sha(match/'classes.json')==r['classes_sha256']
 groups=collections.defaultdict(lambda:collections.defaultdict(set))
 for row in json.loads((inv/'owners.json').read_text()):
  if row['role']=='SOURCE':
   for n in row['net_ids']:groups[row['class_node']][n].add((row['class_node'],row['ptc']))
 rows=json.loads((match/'classes.json').read_text());assert {v['class_node'] for v in rows}==set(groups)
 failures=0;counts=collections.Counter();deficits=collections.Counter();certificates=[]
 for row in rows:
  candidates=groups[row['class_node']];result=row['result'];assert row['net_count']==len(candidates)
  counts[result['status']+'_classes']+=1;counts[result['status']+'_nets']+=len(candidates)
  if result['status']=='infeasible':
   h=result['hall_witness'];requests=h['request_ids'];assert requests and len(requests)==len(set(requests));assert set(requests)<=candidates.keys()
   union={p for n in requests for p in candidates[n]};assert union=={tuple(p) for p in h['physical_pins']}
   assert len(requests)>len(union) and h['deficiency']==len(requests)-len(union)
   certificates.append({'class_node':row['class_node'],'witness_networks':len(requests),'neighbor_pins':len(union),'deficiency':h['deficiency']});deficits[h['deficiency']]+=1;failures+=1
  else:
   assert result['status']=='matched';assignment={int(n):tuple(p) for n,p in result['assignment'].items()};assert set(assignment)==set(candidates)
   assert len(set(assignment.values()))==len(assignment) and all(pin in candidates[n] for n,pin in assignment.items())
 assert dict(counts)==r['counts'] and failures==3170
 out=BASE/'observed_opin_hall_certificate_check';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes());(out/'certificates.json').write_text(json.dumps(certificates)+'\n')
 receipt={'matching_receipt_sha256':sha(match/'receipt.json'),'source_sha256':sha(pathlib.Path(__file__)),'certificates_sha256':sha(out/'certificates.json'),'independently_checked_hall_failures':failures,'counts':dict(counts),'deficiency_histogram':dict(sorted(deficits.items())),'reasoning':'Any nonempty pairwise disjoint per-net OPIN subsets permit choosing one representative per net. Hall deficiency disproves such representatives, hence also disproves those subsets within supplied candidates.','scope':'observed candidate sets only; no full-class infeasibility, reachability or strict-budget certificate; success not joint routing proof'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'hall_failures':failures,'deficiency_histogram':receipt['deficiency_histogram']}))
if __name__=='__main__':main()
