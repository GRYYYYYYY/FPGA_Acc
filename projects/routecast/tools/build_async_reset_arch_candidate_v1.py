import copy,json,sys,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
src=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml';out=R/'experiments/async_reset_arch_candidate_v1_2026-10-08';out.mkdir();tree=E.parse(src);root=tree.getroot();parents={c:p for p in root.iter() for c in p};ffs=[p for p in root.iter('pb_type') if p.get('blif_model')=='.latch'];assert len(ffs)==3
for cell in ['$_DFF_PP0_','$_DFF_PP1_']:
 model=E.SubElement(root.find('models'),'model',name=cell);ip=E.SubElement(model,'input_ports');E.SubElement(ip,'port',name='C',is_clock='1');E.SubElement(ip,'port',name='D',clock='C');E.SubElement(ip,'port',name='R',combinational_sink_ports='Q');op=E.SubElement(model,'output_ports');E.SubElement(op,'port',name='Q',clock='C')
for ff in ffs:
 parent=parents[ff];regular=copy.deepcopy(ff);ff.attrib.pop('blif_model');ff.attrib.pop('class');ff[:]=[]
 for tag,name in [('input','D'),('input','R'),('output','Q'),('clock','clk')]:E.SubElement(ff,tag,name=name,num_pins='1')
 for mode_name,model in [('ordinary','.latch'),('reset_zero','.subckt $_DFF_PP0_'),('reset_one','.subckt $_DFF_PP1_')]:
  mode=E.SubElement(ff,'mode',name=mode_name);leaf=E.SubElement(mode,'pb_type',name='storage',blif_model=model,num_pb='1',**({'class':'flipflop'} if mode_name=='ordinary' else {}))
  E.SubElement(leaf,'input',name='D',num_pins='1');E.SubElement(leaf,'output',name='Q',num_pins='1');clk='clk' if mode_name=='ordinary' else 'C';E.SubElement(leaf,'clock',name=clk,num_pins='1')
  if mode_name=='ordinary':
   leaf.find('input').set('port_class','D');leaf.find('output').set('port_class','Q');leaf.find('clock').set('port_class','clock')
  else:E.SubElement(leaf,'input',name='R',num_pins='1');E.SubElement(leaf,'delay_constant',max='60.32e-12',in_port='storage.R',out_port='storage.Q')
  E.SubElement(leaf,'T_setup',value='18.91e-12',port='storage.D',clock=clk);E.SubElement(leaf,'T_clock_to_Q',max='60.32e-12',port='storage.Q',clock=clk)
  inter=E.SubElement(mode,'interconnect')
  for name,source,dest in [('data','ff.D','storage.D'),('output','storage.Q','ff.Q'),('clock','ff.clk','storage.'+clk)]:E.SubElement(inter,'direct',name=name,input=source,output=dest)
  if mode_name!='ordinary':E.SubElement(inter,'direct',name='reset',input='ff.R',output='storage.R')
 E.SubElement(parent.find('interconnect'),'complete',name='async_reset_input_candidate',input=parent.get('name')+'.in',output='ff.R')
p=out/'architecture.xml';tree.write(p,encoding='unicode');record=dict(bindings={str(src):sha(src),str(Path(__file__)):sha(Path(__file__)),str(p):sha(p)},wrapped_original_FF_locations=len(ffs),added_models=['$_DFF_PP0_','$_DFF_PP1_'],scope='Experimental architecture hypothesis only, not original COFFE architecture or measured silicon. Asynchronous-reset primitive names/ports preserved. Reset arc timing placeholder borrows FF clock-to-Q, no characterized recovery/removal or performance claim. No netlist rewriting, original HDL equivalence or complete native/STA correctness claim. All future comparisons must use this same architecture and explicit timing limitations.');(out/'receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(p)
