"""Freeze/select compatible swaps with exactly unchanged endpoint-net HPWL."""
from collections import defaultdict
from itertools import combinations
import json,re,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha,placements,physical_maps

out=Path('experiments/matched_hpwl_candidates_2026-10-04')
if out.exists():raise ValueError('fresh output required')
base=Path('experiments/pre_route_endpoints_2026-10-04');ep=json.loads((base/'diffeq_endpoints.json').read_text());paths={k:Path(v['path']) for k,v in ep['inputs'].items()};paths['mapping']=base/'diffeq_mapping.json';paths['endpoints']=base/'diffeq_endpoints.json'
out.mkdir();(out/'source').mkdir()
for n in ('matched_hpwl_candidates.py','pre_route_endpoints.py'):shutil.copyfile(Path(__file__).with_name(n),out/'source'/n)
p={'scope':'predictor-independent pre-route candidate control, no native outcomes used','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()},'selection':'all compatible CLB pair swaps with HPWL delta exactly zero; first 8 in packed-order enumeration','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
slots=placements(paths['place'],sha(paths['net']));_,grid,_=physical_maps(paths['graph']);groups=defaultdict(list)
for block in ET.parse(paths['net']).getroot().findall('block'):
    logical=re.sub(r'\[\d+\]$','',block.attrib['instance']);name=block.attrib['name']
    if logical=='clb':
        x,y,z,layer,_=slots[name];groups[(logical,z,layer,grid[(x,y,layer)][0])].append(name)
netids={r['net_id'] for r in ep['connections']};nets=defaultdict(set);touches=defaultdict(set)
for r in json.loads(paths['mapping'].read_text())['pin_details']:
    if r['net_id'] in netids:nets[r['net_id']].add(r['block']);touches[r['block']].add(r['net_id'])
def hpwl(nodes,swap=None):
    coords=[]
    for n in nodes:
        target=(swap[1] if n==swap[0] else swap[0] if n==swap[1] else n) if swap else n
        coords.append(slots[target][:2])
    return max(x for x,y in coords)-min(x for x,y in coords)+max(y for x,y in coords)-min(y for x,y in coords)
initial={n:hpwl(v) for n,v in nets.items()};matched=[];examined=0
for names in groups.values():
    for a,b in combinations(names,2):
        examined+=1;affected=touches[a]|touches[b]
        delta=sum(hpwl(nets[n],(a,b))-initial[n] for n in affected)
        if delta==0:matched.append({'pair':[a,b],'hpwl_delta':0,'affected_nets':len(affected)})
result={'protocol_sha256':sha(out/'protocol.json'),'baseline_hpwl':sum(initial.values()),'examined_compatible_pairs':examined,'matched_pairs':matched,'selected':matched[:8],'scope':p['scope']}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='matched_pairs'}))
