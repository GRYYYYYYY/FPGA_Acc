"""Freeze deterministic consecutive compatible swaps without outcome selection."""
import json,re,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import placements,physical_maps,extract,sha
from affected_connections import affected


def main():
 base=Path('experiments');front=base/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits';out=base/'adder_tree_2L032_move_sequence_2026-10-06'
 p=json.loads((front/'protocol.json').read_text());r=json.loads((front/'receipt.json').read_text());assert sha(front/'protocol.json')==r['protocol_sha256'];assert sha(front/'endpoints.json')==r['outputs']['endpoints.json']
 inputs=p['inputs'];assert all(sha(v['path'])==v['sha256'] for v in inputs.values());before=json.loads((front/'endpoints.json').read_text());assert before['nonclock_global_excluded_net_ids']==[]
 net=Path(inputs['packed_netlist']['path']);graph=Path(inputs['rr_graph']['path']);place=Path(inputs['reference_place']['path']);coords=placements(place,sha(net));types,grid,_=physical_maps(graph)
 cohorts={}
 for block in ET.parse(net).getroot().findall('block'):
  name=block.attrib['name'];kind=re.sub(r'\[\d+\]$','',block.attrib['instance'])
  if kind!='clb':continue
  x,y,z,layer,_=coords[name];signature=(kind,z,layer,grid[(x,y,layer)][0]);cohorts.setdefault(signature,[]).append(name)
 chosen=next(v[:4] for v in cohorts.values() if len(v)>=4)
 pairs=[chosen[:2],chosen[2:4],chosen[:2]]
 out.mkdir();(out/'source').mkdir()
 for name in ('prepare_adder_tree_move_sequence.py','pre_route_endpoints.py','affected_connections.py'):shutil.copyfile(Path('tools')/name,out/'source'/name)
 protocol={'inputs':inputs,'pairs':pairs,'selection':'first compatible packed-order four CLBs; swap first pair, second pair, then undo first pair; no metric or route input','sources_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'frontend_receipt_sha256':sha(front/'receipt.json')};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');steps=[]
 for i,pair in enumerate(pairs,1):
  old_coords=placements(place,sha(net));lines=[]
  for line in place.read_text().splitlines():
   fields=line.split()
   if fields and fields[0] in pair:
    name=fields[0];other=pair[1] if name==pair[0] else pair[0];x,y,z,layer,_=old_coords[other];line=f'{name}\t{x}\t{y}\t{z}\t{layer}\t#{old_coords[name][4]}'
   lines.append(line)
  moved=out/f'step_{i}.place';moved.write_text('\n'.join(lines)+'\n');after,mapping=extract(net,moved,graph);after['nonclock_global_excluded_net_ids']=[]
  assert {(v['connection_id'],v['net_id']) for v in before['connections']}=={(v['connection_id'],v['net_id']) for v in after['connections']}
  closure=affected(before,after);(out/f'step_{i}_endpoints.json').write_text(json.dumps(after,indent=2)+'\n');(out/f'step_{i}_mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');(out/f'step_{i}_closure.json').write_text(json.dumps(closure,indent=2)+'\n')
  fresh=placements(moved,sha(net));assert all(fresh[n]==old_coords[n] for n in fresh if n not in pair)
  assert all(fresh[pair[j]][:4]==old_coords[pair[1-j]][:4] and fresh[pair[j]][4]==old_coords[pair[j]][4] for j in (0,1))
  item={'step':i,'pair':pair,'changed':len(closure['changed_connection_ids']),'recompute':len(closure['recompute_connection_ids']),'retained':len(closure['retained_connection_ids']),'outputs_sha256':{f'step_{i}{suffix}':sha(out/f'step_{i}{suffix}') for suffix in ('.place','_endpoints.json','_mapping.json','_closure.json')}};steps.append(item);print(json.dumps(item),flush=True);before=after;place=moved
 assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'steps':steps,'scope':'actual consecutive endpoint changes, no native legality, full-search parity or benefit yet'},indent=2)+'\n')

if __name__=='__main__':main()
