"""Necessary class-capacity conditions including excluded logical pin demands."""
import pathlib,json,array,hashlib,sys,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 front=BASE/'endpoints_undriven_v2';csr=BASE/'streaming_csr_class_cache_v3/csr';parent=BASE/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host'
 mapping=front/'mapping.json';endpoint=front/'endpoints.json';m=json.loads((csr/'manifest.json').read_text());p=json.loads((parent/'protocol.json').read_text())
 assert sha(csr/'manifest.json')==p['csr_manifest_sha256'];assert sha(mapping)=='1d5eade4989216c49450de200e39eb65b41f80de1537cbd580e5ec47d2b3bbb2';assert sha(endpoint)==p['inputs']['endpoints']['sha256']
 files=[mapping,endpoint,csr/'manifest.json'];hashes={str(f):sha(f) for f in files};data={}
 for key in ['node_ids','types','capacities']:
  spec=m['files'][key];f=csr/spec['file'];h=sha(f);assert h==spec['sha256'];hashes[str(f)]=h;a=array.array(spec['type']);a.frombytes(f.read_bytes())
  if sys.byteorder!='little':a.byteswap()
  assert len(a)==m['nodes'];data[key]=a
 assert all(i==v for i,v in enumerate(data['node_ids']))
 e=json.loads(endpoint.read_text());excluded={v['net_id'] for v in e['excluded_nets']};groups=collections.defaultdict(list)
 for r in json.loads(mapping.read_text())['pin_details']:groups[(r['role'],r['rr_node'])].append(r)
 rows=[];summary=collections.defaultdict(collections.Counter)
 for (role,node),pins in sorted(groups.items()):
  assert data['types'][node]==m['type_codes'][role]
  cap=data['capacities'][node];packed={r['physical_pin_ptc'] for r in pins};assert all(0<=v for v in packed)
  retained=sum(r['net_id'] not in excluded for r in pins);reserved=len(pins)-retained
  row={'role':role,'class_node':node,'capacity':cap,'logical_pin_demands':len(pins),'retained_demands':retained,'excluded_demands':reserved,'distinct_packed_ptcs':len(packed),'repeated_packed_ptcs':len(pins)-len(packed),'demand_excess':max(0,len(pins)-cap),'slack':cap-len(pins)};rows.append(row)
  s=summary[role];s['classes']+=1;s['capacity']+=cap;s['logical_pin_demands']+=len(pins);s['excluded_demands']+=reserved;s['classes_over_capacity']+=len(pins)>cap;s['classes_at_capacity']+=len(pins)==cap;s['classes_with_repeated_packed_ptc']+=len(pins)>len(packed)
 assert sum(v['logical_pin_demands'] for v in summary.values())==149973
 assert all(sha(pathlib.Path(f))==h for f,h in hashes.items())
 out=BASE/'class_pin_capacity_diagnosis';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes());(out/'classes.json').write_text(json.dumps(rows)+'\n')
 result={'inputs_sha256':hashes,'source_sha256':sha(pathlib.Path(__file__)),'classes_sha256':sha(out/'classes.json'),'summary':{k:dict(v) for k,v in summary.items()},'scope':'necessary logical class-capacity conditions, not candidate reachability/Hall feasibility, actual reservation, or legal routing proof'}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
if __name__=='__main__':main()
