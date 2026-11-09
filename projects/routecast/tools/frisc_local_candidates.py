"""Freeze local improving swaps before predictor or native candidate outcomes."""
from collections import defaultdict
from itertools import combinations
import json,re,shutil,random
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha,placements,physical_maps

out=Path('experiments/frisc_local_candidates_2026-10-05')
if out.exists():raise ValueError('fresh output required')
base=Path('experiments/frisc_endpoints_2026-10-05');ep=json.loads((base/'endpoints.json').read_text());paths={k:Path(v['path']) for k,v in ep['inputs'].items()};paths['mapping']=base/'mapping.json';paths['endpoints']=base/'endpoints.json'
out.mkdir();(out/'source').mkdir()
for n in ('frisc_local_candidates.py','pre_route_endpoints.py'):shutil.copyfile(Path(__file__).with_name(n),out/'source'/n)
p={'scope':'predictor-independent pre-route candidate control, no native outcomes used','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()},'selection':'compatible CLB swaps with Manhattan distance <=2 and HPWL delta <0; shuffle eligible pairs with seed20261005 and take first up to8; no threshold relaxation','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
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
        if abs(slots[a][0]-slots[b][0])+abs(slots[a][1]-slots[b][1])<=2 and delta<0:matched.append({'pair':[a,b],'hpwl_delta':delta,'affected_nets':len(affected)})
random.Random(20261005).shuffle(matched)
result={'protocol_sha256':sha(out/'protocol.json'),'baseline_hpwl':sum(initial.values()),'examined_compatible_pairs':examined,'eligible_pairs':matched,'selected':matched[:8],'scope':p['scope']}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
for cid,entry in enumerate(result['selected'],1):
    lines=[];a,b=entry['pair']
    for line in paths['place'].read_text().splitlines():
        fields=line.split()
        if fields and fields[0] in (a,b):
            name=fields[0];target=b if name==a else a;x,y,z,layer,_=slots[target];bid=slots[name][4]
            line=f'{name}\t{x}\t{y}\t{z}\t{layer}\t#{bid}'
        lines.append(line)
    (out/f'candidate_{cid}.place').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='eligible_pairs'}))
