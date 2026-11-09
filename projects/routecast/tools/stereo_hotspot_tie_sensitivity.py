"""Exhaustive top-20 boundary tie sensitivity on authenticated frozen maps."""
import itertools,json,pathlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
SRC=BASE/'ordinary_additive_undriven_v2_authenticated_host_evaluation'
DIAG=BASE/'frozen_spatial_hotspot_diagnosis'
OUT=BASE/'frozen_spatial_hotspot_tie_sensitivity'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 paths=[SRC/'spatial_maps.json',SRC/'receipt.json',DIAG/'report.json',DIAG/'completion.json']
 hashes={str(p):sha(p) for p in paths}
 receipt=json.loads(paths[1].read_text()); prior=json.loads(paths[2].read_text()); completion=json.loads(paths[3].read_text())
 assert hashes[str(paths[0])]==receipt['spatial_maps_sha256']==prior['inputs_sha256']['spatial_maps.json']
 assert hashes[str(paths[2])]==completion['report_sha256']
 maps=json.loads(paths[0].read_text()); sets={}; details={}
 for name in ['prediction','native']:
  values=maps[name]; boundary=prior['top20'][name]['boundary']
  strict={k for k,v in values.items() if v>boundary}
  tied=sorted(k for k,v in values.items() if v==boundary)
  slots=20-len(strict)
  assert slots==1 # This frozen case: 19 mandatory cells on both sides.
  sets[name]=[strict|set(c) for c in itertools.combinations(tied,slots)]
  details[name]={'mandatory_count':len(strict),'boundary_candidates':tied,'boundary_slots':slots,'possible_top20_sets':len(sets[name])}
 counts=[len(a&b) for a in sets['prediction'] for b in sets['native']]
 union={name:set().union(*items) for name,items in sets.items()}
 result={'scope':'posthoc exhaustive boundary-tie sensitivity only; published string-ID metric unchanged; no predictor tuning','input_sha256':hashes,'source_sha256':sha(pathlib.Path(__file__)),'details':details,'enumerated_pairs':len(counts),'minimum_hits':min(counts),'maximum_hits':max(counts),'minimum_precision':min(counts)/20,'maximum_precision':max(counts)/20,'boundary_inclusive_shared_ids':sorted(union['prediction']&union['native']),'hit_count_histogram':{str(v):counts.count(v) for v in sorted(set(counts))}}
 assert all(sha(pathlib.Path(p))==h for p,h in hashes.items())
 OUT.mkdir(exist_ok=True);(OUT/'source').mkdir(exist_ok=True)
 (OUT/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 (OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
 (OUT/'completion.json').write_text(json.dumps({'inputs_unchanged':True,'report_sha256':sha(OUT/'report.json'),'source_sha256':result['source_sha256']},indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['input_sha256','details']}))
if __name__=='__main__':main()
