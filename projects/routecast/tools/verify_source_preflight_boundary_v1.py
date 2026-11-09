"""Independent terminal classification and RAM interface/instance-count checks."""
import json
from pathlib import Path
from collections import Counter
from functools import lru_cache
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/preroute_family_admission_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def integer(v):return int(v,2) if isinstance(v,str) else int(v)
def main():
 interface=load(D/'clock_ram_interface_audit_v2.json');classification=[]
 for version in [1,2,3,4]:
  folder=D/('structure_preflight' if version==1 else f'structure_preflight_v{version}');results=load(folder/'results.json')['results']
  for r in results:
   text=(folder/r['name']/'yosys.log').read_text()
   if version==1:assert r['exit_code']==127 and 'error while loading shared libraries' in text;kind='DYNAMIC_LOADER_FAILURE_BEFORE_HDL'
   elif version==2:assert r['exit_code']==1 and "Can't open script file" in text;kind='COMMAND_PATH_FAILURE_BEFORE_HDL'
   elif r['exit_code']==0:kind='RAW_PROCESS_CHECK_ONLY'
   elif version==3:assert 'dual_port_ram' in text and 'not part of the design' in text;kind='MISSING_PRIMITIVE_SOURCE_CLOSURE'
   else:assert r['exit_code']==-6 and 'std::bad_alloc' in text;kind='FUNCTIONAL_PRIMITIVE_EXPANSION_RESOURCE_FAILURE'
   assert not r['native_architecture_admitted'] and not r['strict_unseen_admitted'];classification.append(dict(version=version,name=r['name'],classification=kind))
 for result in interface['rows']:
  design=load(D/'primitive_interface_probe_v1'/result['name']/'proc.json');modules=design['modules']
  @lru_cache(None)
  def count(module):
   clocked=0;ram=0
   for cell in modules[module].get('cells',{}).values():
    typ=cell['type']
    if typ in ['single_port_ram','dual_port_ram']:
     assert integer(modules[typ]['attributes']['blackbox'])==1;ram+=1;p=cell['parameters'];a=integer(p['ADDR_WIDTH']);w=integer(p['DATA_WIDTH']);con=cell['connections'];assert len(con['clk'])==1
     for name in ['addr'] if typ=='single_port_ram' else ['addr1','addr2']:assert len(con[name])==a
     for name in ['data','out'] if typ=='single_port_ram' else ['data1','data2','out1','out2']:
      if con.get(name):assert len(con[name])==w
    elif typ in modules and not integer(modules[typ].get('attributes',{}).get('blackbox',0)):
     c,r=count(typ);clocked+=c;ram+=r
    elif typ.startswith('$') and 'CLK' in cell.get('connections',{}) and integer(cell.get('parameters',{}).get('CLK_ENABLE',1)):clocked+=1
   return clocked,ram
  clocks,rams=count(result['name']);assert clocks==result['hierarchical_clocked_cell_count'] and rams==len(result['logical_RAM_instances']);assert sum(result['clock_origins_cell_counts'].values())==clocks;assert len(result['clock_origins_cell_counts'])==1;assert not result['target_architecture_admitted']
 assert not list(D.rglob('*.route'))
 out=dict(status='PREFLIGHT_FAILURE_CLASSES_CLOCK_COUNTS_AND_RAM_INTERFACES_RECONCILED',classifications=classification,strict_unseen_admitted=0,new_native_route_labels=False,scope='RAMblackboxinterface and reachableenabledclock counts only. FunctionalRAMresourcefailures remainfailures;not architecture/mapping/HDLbehavioral equivalence proof.',bindings={str(p):sha(p) for p in [D/'clock_ram_interface_audit_v2.json',D/'structure_preflight_manifest_v4.json',D/'primitive_interface_probe_manifest_v1.json',Path(__file__)]})
 with (D/'independent_preflight_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'])
if __name__=='__main__':main()
