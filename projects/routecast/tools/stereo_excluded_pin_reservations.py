"""Pre-route logical reservation inventory; never asserts physical routed ownership."""
import pathlib,json,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 front=BASE/'endpoints_undriven_v2';wdir=BASE/'full_path_pin_witness'
 files=[front/'endpoints.json',front/'mapping.json',wdir/'witness.json',wdir/'receipt.json'];hashes={str(p):sha(p) for p in files}
 endpoints=json.loads(files[0].read_text());mapping=json.loads(files[1].read_text());receipt=json.loads(files[3].read_text())
 assert hashes[str(files[0])]=='c493b5e282e166f12a222d149a0cc9fe43c4bf590e7acd9a7b818aa3d8c247ae'
 assert hashes[str(files[1])]==receipt['inputs_sha256'][str(files[1])]
 assert hashes[str(files[2])]==receipt['witness_sha256']
 excluded={r['net_id']:r for r in endpoints['excluded_nets']};retained={r['net_id'] for r in endpoints['connections']};assert not retained&excluded.keys()
 rows=[r for r in mapping['pin_details'] if r['net_id'] in excluded]
 reservations=collections.defaultdict(list);counts=collections.defaultdict(collections.Counter)
 for r in rows:
  key=(r['role'],r['rr_node'],r['physical_pin_ptc']);reservations[key].append(r)
  counts[r['net_id']][r['role']]+=1
 for n,r in excluded.items():assert counts[n]['SINK']==r['sink_pins']
 witness=json.loads(files[2].read_text());matches=[];byrole=collections.Counter();nets=set();pins=set()
 for r in witness:
  key=(r['role'],r['class_node'],r['actual_ptc'])
  if key in reservations:
   matches.append({'connection_id':r['connection_id'],'net_id':r['net_id'],'role':r['role'],'actual_pin_node':r['actual_pin_node'],'excluded_net_ids':sorted({v['net_id'] for v in reservations[key]})})
   byrole[r['role']]+=1;nets.add(r['net_id']);pins.add(r['actual_pin_node'])
 assert all(sha(pathlib.Path(p))==h for p,h in hashes.items())
 out=BASE/'excluded_logical_pin_reservations';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 (out/'reservations.json').write_text(json.dumps(rows)+'\n');(out/'packed_binding_matches.json').write_text(json.dumps(matches)+'\n')
 result={'inputs_sha256':hashes,'source_sha256':sha(pathlib.Path(__file__)),'reservations_sha256':sha(out/'reservations.json'),'matches_sha256':sha(out/'packed_binding_matches.json'),'excluded_nets':len(excluded),'excluded_pin_details':len(rows),'by_net':{str(n):dict(c) for n,c in counts.items()},'matching_predicted_connection_sides':dict(byrole),'matching_retained_nets':len(nets),'matching_actual_pins':len(pins),'scope':'pre-route packed logical reservations only; predicted pin matching packed excluded binding is not proof of actual routed conflict; no native labels used'}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['inputs_sha256','source_sha256','reservations_sha256','matches_sha256']}))
if __name__=='__main__':main()
