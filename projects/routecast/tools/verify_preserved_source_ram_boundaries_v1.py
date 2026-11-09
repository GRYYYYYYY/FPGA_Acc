"""Preserved source primitive interface audit; no behavioral equivalence claim."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];D=R/'experiments/preserved_source_ram_mapping_v1_2026-10-21';A=R/'experiments/preroute_family_admission_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def integer(x):return int(x,2) if isinstance(x,str) else x
def main():
 protocol=json.loads((D/'protocol.json').read_text())
 for p,h in protocol['bindings'].items():assert sha(Path(p))==h,p
 interface=json.loads((A/'clock_ram_interface_audit_v2.json').read_text());expected={r['name']:r['logical_RAM_instances'] for r in interface['rows']};results=json.loads((D/'results.json').read_text())['rows'];rows=[]
 for row in results:
  name=row['case'];f=D/name;file=f/'preserved_boundary.json';assert file.exists();design=json.loads(file.read_text());top=design['modules'][name];found=[]
  for cellname,c in top['cells'].items():
   typ=c['type'];model='dual_port_ram' if typ.endswith('dual_port_ram') else ('single_port_ram' if typ.endswith('single_port_ram') else None)
   if model is None:continue
   mod=design['modules'][typ];assert integer(mod['attributes']['keep_hierarchy'])==1;assert not integer(mod['attributes'].get('blackbox','0'));z=c['connections'];addr='addr1' if model=='dual_port_ram' else 'addr';data='data1' if model=='dual_port_ram' else 'data';a,w=len(z[addr]),len(z[data]);assert integer(mod['parameter_default_values']['ADDR_WIDTH'])==a and integer(mod['parameter_default_values']['DATA_WIDTH'])==w
   clk=z['clk'];assert len(clk)==1 and any(clk==p['bits'] for p in top['ports'].values() if p['direction']=='input')
   if model=='dual_port_ram':assert z['we2']==['0'] and len(z['addr2'])==a and len(z['data2'])==w
   found.append({'instance':cellname,'model':model,'address_bits':a,'data_bits':w})
  key=lambda x:(x['model'],x['address_bits'],x['data_bits']);assert Counter(map(key,found))==Counter(map(key,expected[name]))
  command=(f/'commands.ys').read_text();assert 'setattr -mod -set keep_hierarchy 1 single_port_ram dual_port_ram' in command;assert 'async2sync' not in command and 'adff2dff' not in command and '-lib ' not in command
  log=(f/'yosys.log').read_text();rows.append({'case':name,'preserved_RAM_interfaces':found,'mapper_exit_code':row['exit_code'],'structural_mapping_passed':row['exit_code']==0,'mapped_cell_types':row.get('mapped_types'), 'bindings':{str(p.relative_to(R)):sha(p) for p in [file,f/'commands.ys',f/'yosys.log']}})
 out={'status':'PRESERVED_REAL_SOURCE_RAM_BOUNDARIES_VERIFIED','rows':rows,'scope':'Exact shape multiset against earlier source-interface audit, functional-module hierarchy attributes, literal second-write disables and direct top-input clocks. Library bodies are not qualified semantic IR. No full-source/reset/behavioral/packing/route admission.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
