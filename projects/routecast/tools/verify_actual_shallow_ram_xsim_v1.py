"""Independently bind every extracted physical RAM pin and classify HDL coverage."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'actual_shallow_ram_xsim_v1_2026-10-21';P=E/'shallow_ram_address_completion_v1_2026-10-21';B=E/'parmys_source_provenance_replay_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p,h in json.loads((D/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 rows=json.loads((D/'results.json').read_text())['rows'];assert len(rows)==3 and all(r['exit_code']==0 for r in rows);log=(D/'xsim.log').read_text();assert 'ALL_SHALLOW_GROUPS_COMPLETE' in log and 'Fatal:' not in log
 fixtures=(D/'fixtures.v').read_text();extracted=json.loads((D/'extraction_manifest.json').read_text())['groups'];assert len(extracted)==12;designs={n:json.loads((P/n/'candidate.json').read_text())['modules'][n] for n in ['mcml','mkDelayWorker32B']};prov={(r['source'],g['source_instance']):g for r in json.loads((B/'verification_v1.json').read_text())['rows'] for g in r['groups']};reports=[]
 for g in extracted:
  idx=g['group'];block=fixtures.split(f'module checker{idx}(',1)[1].split('endmodule',1)[0];m=designs[g['source']];source=prov[g['source'],g['instance']];assert set(g['physical_lanes'].values())==set(source['descendant_cells']);assert set(map(int,g['physical_lanes']))==set(range(g['width']));rename={int(k):v for k,v in g['input_node_renaming'].items()};assert len(set(rename.values()))==len(rename)
  def bit(b):return rename[b] if isinstance(b,int) else "1'b"+b
  def vec(bs):return '{'+','.join(bit(b) for b in reversed(bs))+'}'
  for lane,name in g['physical_lanes'].items():
   c=m['cells'][name];dp=c['type']=='dual_port_ram';pins=[]
   for port,bs in c['connections'].items():
    expected=f'phy{1 if port in ["out","out1"] else 2}[{lane}]' if c['port_directions'][port]=='output' else vec(bs);pins.append('.'+port+'('+expected+')')
   expected=f'{c["type"]} #(.ADDR_WIDTH(11),.DATA_WIDTH(1)) lane{lane}('+','.join(pins)+');';assert expected in block,(idx,lane)
  first=m['cells'][next(iter(g['physical_lanes'].values()))];z=first['connections'];we=z['we1' if dp else 'we'];assert g['read_only']==(we==['0']);assert vec(we)==("{1'b0}" if g['read_only'] else '{we}')
  assert 'reference(' in block
  assert ('.data1(effective_data)' if dp else '.data(effective_data)') in block
  if g['read_only']:assert f'SHALLOW_RO_UNINITIALIZED_ONLY group={idx} cycles=512 writes=0' in log
  else:assert f'SHALLOW_WRITABLE_TRACE_PASS group={idx} initialized_rows={1<<g["address_bits"]} cycles=512' in log
  reports.append({'group':idx,'source':g['source'],'instance':g['instance'],'width':g['width'],'logical_rows':1<<g['address_bits'],'public_initialization_writes':0 if g['read_only'] else 1<<g['address_bits'],'defined_read_write_cycles':0 if g['read_only'] else 512,'uninitialized_read_only_cycles':512 if g['read_only'] else 0,'all_physical_pins_exact_under_input_renaming':True})
 assert sum(r['defined_read_write_cycles'] for r in reports)==4608;assert sum(r['uninitialized_read_only_cycles'] for r in reports)==1536
 out={'status':'ACTUAL_SHALLOW_RAM_HDL_TRACE_RECEIPTS_AND_PHYSICAL_PINS_VERIFIED','groups':reports,'known_data_writable_groups':9,'uninitialized_only_readonly_groups':3,'public_initialization_writes':sum(r['public_initialization_writes'] for r in reports),'defined_read_write_cycles':4608,'bindings':{str(p.relative_to(R)):sha(p) for p in [D/'fixtures.v',D/'extraction_manifest.json',D/'xsim.log',D/'results.json']},'scope':'Actual physical pin/constant/lane fixtures under local input renaming. Upstream source state/control is abstracted.9writable groups no cross-port collisions.3readonly groups do not establish contents, intended lookup function, arbitrary initialized-state correspondence or complete source equivalence.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
