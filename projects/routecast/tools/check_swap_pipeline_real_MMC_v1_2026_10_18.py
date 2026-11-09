"""Real exposed development placement format check, without new routing or scoring."""
import sys,json,re,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import placements,sha
from prospective_layout_swap_apply_v1 import make_episodes

def main():
 base=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed';net=base/'demand/mmc/design.net';place=base/'demand/mmc/design.place';graph=base/'rr/mmc/rr_graph.xml'
 source_paths=[net,place,graph,Path(__file__),R/'tools/pre_route_endpoints.py',R/'tools/prospective_layout_swap_apply_v1.py',R/'tools/prospective_layout_swap_selection_v1.py'];bindings={str(p):sha(p) for p in source_paths};assert bindings[str(graph)]=='8d13c26981fbc46df4ae4584b848863cff89f711e6f2b30f396638fd8d7db131'
 positions=placements(place,bindings[str(net)]);root=ET.parse(net).getroot();blocks={b.get('name'):b for b in root.findall('block')};assert set(positions)==set(blocks)
 types={};grid={}
 for event,e in ET.iterparse(graph,events=['end']):
  if e.tag=='block_type':types[int(e.get('id'))]=e.get('name')
  if e.tag=='grid_loc':
   key=tuple(int(e.get(k,'0')) for k in ['x','y','layer']);assert key not in grid;grid[key]=tuple(int(e.get(k,'0')) for k in ['block_type_id','width_offset','height_offset'])
  if e.tag=='grid':break
 records=[]
 for name,(x,y,z,layer,bid) in positions.items():
  tid,wo,ho=grid[x,y,layer];assert wo==ho==0
  logical=re.sub(r'\[\d+\]$','',blocks[name].get('instance'));physical=types[tid];assert logical==physical
  records.append(dict(name=name,logical_type=logical,location=[x,y,z,layer],physical_type=physical,subtile=z))
 result=make_episodes(records);assert result['selection']['selected']==3
 out=R/'experiments/prospective_layout_swap_real_MMC_v1_2026-10-18';out.mkdir(exist_ok=False);checks=[]
 for ep in result['episodes']:
  rows={r['name']:r['location'] for r in ep['blocks']};lines=[]
  for line in place.read_text().splitlines():
   t=line.split()
   if t and t[0] in rows:
    assert len(t)==6;t[1:5]=map(str,rows[t[0]]);line='\t'.join(t)
   lines.append(line)
  output=out/f'episode_{ep["episode"]:02}.place';output.write_text('\n'.join(lines)+'\n');readback=placements(output,bindings[str(net)]);a,b=ep['changed_blocks'];expected=dict(positions);expected[a]=(*positions[b][:4],positions[a][4]);expected[b]=(*positions[a][:4],positions[b][4]);assert readback==expected
  checks.append(dict(episode=ep['episode'],changed_blocks=[a,b],file=str(output),sha256=sha(output),all_other_block_rows_equal=True))
 # Pin legality and native acceptance are explicitly not implied by site occupancy.
 assert sha(net)==bindings[str(net)] and sha(place)==bindings[str(place)]
 receipt=dict(status='real_MMC_source_layout_three_independent_swaps_roundtrip_verified',bindings=bindings,blocks=len(records),CLB_blocks=sum(r['logical_type']=='clb' for r in records),episodes=checks,scope='Already exposed development source only. Complete placement names, native netlist ID and exact RR graph bound; tile type/root and occupied slots checked, serialized files reparsed against independent expected coordinate dictionaries. No route or score computed. This is not full physical pin legality, native placer acceptance, strict-family admission or a new forecasting experiment.')
 with (out/'verification.json').open('x') as f:json.dump(receipt,f,indent=2)
 print('REAL MMC SWAP ROUNDTRIP PASS',len(records),len(checks),flush=True)
if __name__=='__main__':main()
