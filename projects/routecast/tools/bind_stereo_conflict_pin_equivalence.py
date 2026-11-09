"""Architecture/packed logical binding for five conflict requests, not free pins."""
import json,re,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'conflict_pin_equivalence_binding';out.mkdir()
 p=json.loads((b/'endpoints_undriven_v2/protocol.json').read_text());inputs=p['inputs'];files={k:inputs[k] for k in ('architecture','packed_netlist')}
 mapping=b/'endpoints_undriven_v2/mapping.json';reqpath=b/'additional_high_fanout_physical_audit/conflict_repair_requests.json'
 bound={str(mapping):sha(mapping),str(reqpath):sha(reqpath)}
 assert bound[str(mapping)]=='1d5eade4989216c49450de200e39eb65b41f80de1537cbd580e5ec47d2b3bbb2'
 for v in files.values():assert sha(v['path'])==v['sha256'];bound[v['path']]=v['sha256']
 source=sha(__file__);shutil.copyfile(__file__,out/Path(__file__).name)
 rows=json.loads(mapping.read_text())['pin_details'];requests=json.loads(reqpath.read_text())['requests'];selected=[]
 for q in requests:
  hits=[x for x in rows if x['net_id']==q['net_id'] and x['rr_node']==q['sink'] and x['role']=='SINK']
  if len(hits)!=1:raise ValueError('ambiguous logical target')
  selected.append((q,hits[0]))
 wanted={r['block'] for _,r in selected};blocks={};depth=0
 for event,e in ET.iterparse(files['packed_netlist']['path'],events=('start','end')):
  if event=='start':depth+=1;continue
  if depth==2 and e.tag=='block':
   if e.get('name') in wanted:
    if e.get('name') in blocks:raise ValueError('duplicate packed block')
    blocks[e.get('name')]=e.get('instance').split('[')[0]
   e.clear()
  depth-=1
 arch=ET.parse(files['architecture']['path']).getroot();result=[]
 for q,r in selected:
  kind=blocks[r['block']];logical=arch.findall('./complexblocklist/pb_type[@name="'+kind+'"]');ports=[x for pb in logical for x in pb.findall('./input') if x.get('name')==r['port']]
  tiles=[(tile,sub,port) for tile in arch.findall('./tiles/tile') for sub in tile.findall('./sub_tile') if any(site.get('pb_type')==kind for site in sub.findall('./equivalent_sites/site')) for port in sub.findall('./input') if port.get('name')==r['port']]
  if len(ports)!=1 or len(tiles)!=1:raise ValueError('ambiguous architecture binding')
  tile,sub,port=tiles[0];eq=ports[0].get('equivalent','none');physical=port.get('equivalent','none')
  if eq!=physical:raise ValueError('logical/physical equivalence mismatch')
  result.append({'connection_id':q['connection_id'],'mapping':r,'logical_block_type':kind,'logical_equivalent':eq,'tile':tile.get('name'),'sub_tile':sub.get('name'),'tile_equivalent':physical,'num_pins':int(port.get('num_pins'))})
 if any(sha(k)!=v for k,v in bound.items()) or sha(__file__)!=source:raise ValueError('changed inputs')
 (out/'binding.json').write_text(json.dumps({'inputs':bound,'source_sha256':source,'requests':result,'scope':'logical/architecture declaration binding only; RR members, actual unused ownership and candidate paths still required'},indent=2)+'\n')
 print(json.dumps({'requests':len(result),'equivalence':[x['logical_equivalent'] for x in result],'binding_sha256':sha(out/'binding.json')}),flush=True)
if __name__=='__main__':run()
