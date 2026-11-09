"""Reachable hierarchical clock origins and logical RAM versus physical shapes."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/preroute_family_admission_v1_2026-10-20';P=D/'primitive_interface_probe_v1';ARCH=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
def load(p):return json.loads(p.read_text())
def integer(v):return int(v,2) if isinstance(v,str) else int(v)
def main():
 root=ET.parse(ARCH).getroot();shapes={name:[] for name in ['single_port_ram','dual_port_ram']}
 for pb in root.iter('pb_type'):
  model=pb.get('blif_model','').removeprefix('.subckt ')
  if model not in shapes:continue
  pins={p.get('name'):int(p.get('num_pins')) for p in pb if p.tag in ['input','output','clock']};shapes[model].append(dict(name=pb.get('name'),address_bits=pins['addr1' if model=='dual_port_ram' else 'addr'],data_bits=pins['data1' if model=='dual_port_ram' else 'data']))
 results=[];bindings={str(ARCH):sha(ARCH),str(D/'primitive_interface_probe_manifest_v1.json'):sha(D/'primitive_interface_probe_manifest_v1.json'),str(Path(__file__)):sha(__file__)}
 for name in ['mcml','arm_core','mkDelayWorker32B']:
  path=P/name/'proc.json';modules=load(path)['modules'];terminal=load(P/name/'terminal.json');assert terminal['exit_code']==0;top=modules[name];clock_cells=Counter();clock_bits=Counter();ram=[];seqcells=seqbits=0;memory_bits=0
  rootmap={b:f'{port}[{i}]' for port,p in top['ports'].items() if p['direction']=='input' for i,b in enumerate(p['bits'])}
  def visit(module,bind,context,stack):
   nonlocal seqcells,seqbits,memory_bits
   assert module not in stack;obj=modules[module]
   def origin(bit):return bind.get(bit,'constant:'+bit if isinstance(bit,str) else 'derived_or_internal:'+context+':'+str(bit))
   for mem in obj.get('memories',{}).values():memory_bits+=mem['width']*mem['size']
   for cellname,cell in obj.get('cells',{}).items():
    typ=cell['type'];where=context+'/'+cellname
    if typ in shapes:
     con=cell['connections'];addr='addr1' if typ=='dual_port_ram' else 'addr';data='data1' if typ=='dual_port_ram' else 'data';a=len(con[addr]);w=len(con[data]);ap=integer(cell['parameters']['ADDR_WIDTH']);wp=integer(cell['parameters']['DATA_WIDTH']);assert (a,w)==(ap,wp);fits=any(s['address_bits']>=a and s['data_bits']>=w for s in shapes[typ]);ram.append(dict(instance=where,model=typ,address_bits=a,data_bits=w,declared_storage_bits=(1<<a)*w,clock_origins=[origin(b) for b in con['clk']],fits_one_native_mode_after_depth_padding=fits,requires_decomposition_or_other_mapping=not fits));continue
    if typ.startswith('$') and 'CLK' in cell.get('connections',{}) and integer(cell.get('parameters',{}).get('CLK_ENABLE',1)) != 0:
     width=integer(cell.get('parameters',{}).get('WIDTH',1));seqcells+=1;seqbits+=width
     for b in cell['connections']['CLK']:clock_cells[origin(b)]+=1;clock_bits[origin(b)]+=width
    if typ in modules and not integer(modules[typ].get('attributes',{}).get('blackbox',0)):
     child={}
     for port,p in modules[typ].get('ports',{}).items():
      if p['direction']!='input':continue
      wires=cell['connections'].get(port,[]);assert len(wires)==len(p['bits'])
      child.update((local,origin(parent)) for local,parent in zip(p['bits'],wires))
     visit(typ,child,where,stack+(module,))
  visit(name,rootmap,name,());results.append(dict(name=name,hierarchical_clocked_cell_count=seqcells,clocked_width_sum=seqbits,clock_origins_cell_counts=dict(clock_cells),clock_origins_width_sums=dict(clock_bits),logical_RAM_instances=ram,declared_internal_memory_bits=memory_bits,target_architecture_admitted=False,source_behavioral_equivalence_proven=False));bindings[str(path)]=sha(path);print('CLOCK_RAM_INTERFACE',name,'clockedcells',seqcells,'clocks',dict(clock_cells),'RAMs',len(ram),'needdecomposition',sum(r['requires_decomposition_or_other_mapping'] for r in ram))
 out=dict(status='REACHABLE_CLOCK_ORIGINS_AND_LOGICAL_RAM_PORT_SHAPES_AUDITED',rows=results,native_RAM_shapes=shapes,strict_unseen_admitted=0,scope='Interface-only primitive boxes;disabled CLK_ENABLE=0 memory ports excluded from activeclock counts (v1retained for diagnosis). WIDTH sums/declaredstorage are preoptimization structural quantities,not synthesized FFcount or guaranteed block lowerbounds. No memory collision/reset behavior proof,legal packing,clock STA or native result.',bindings=bindings)
 with (D/'clock_ram_interface_audit_v2.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
if __name__=='__main__':main()
