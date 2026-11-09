"""Isolated experimental PN modes; preserve all existing architecture content."""
import copy,json,xml.etree.ElementTree as ET
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_direct_pn_arch_v1_2026-10-20'
def main():
 source=E/'async_reset_arch_candidate_v2_2026-10-08/architecture.xml';proof=E/'prince_reset_event_sim_v1_2026-10-20/research_decision_v1.json';net=E/'prince_compile_cut_v2_2026-10-20/design.blif';D.mkdir(exist_ok=False);root=ET.parse(source).getroot();original=ET.tostring(root);models=root.find('models');added=[];locations=[];pairs=[('$_DFF_PP0_','$_DFF_PN0_','reset_zero','negative_reset_zero'),('$_DFF_PP1_','$_DFF_PN1_','reset_one','negative_reset_one')]
 (D/'protocol.json').write_text(json.dumps({'status':'FROZEN_DIRECT_PN_ARCH_EXTENSION_BEFORE_PACK','policy':'Clone existing experimental PP async architecture. Append PN model copies and6 matching storage modes at same3 FF locations. Only model/mode identifiers differ; original clock/reset netlist and all existing architecture elements immutable. No inverter, async2sync or reset-clock assumptions.','scope':'Experimental architecture syntax/packing interface, not original COFFE or characterized reset timing. Existing reset timing placeholders explicitly inherited; no native route labels, CPD or physical hardware claims. Original mapped PN netlist used unchanged.','bindings':{str(p):sha(p) for p in [Path(__file__),source,proof,net]}},indent=2)+'\n')
 for old,new,_,_ in pairs:
  assert models.find("model[@name='"+new+"']") is None;node=copy.deepcopy(models.find("model[@name='"+old+"']"));assert node is not None;node.set('name',new);models.append(node);added.append(node)
 for pb in root.iter('pb_type'):
  oldmodes={m.get('name'):m for m in pb.findall('mode')}
  if not {'reset_zero','reset_one'}<=set(oldmodes):continue
  for old,new,oldmode,newmode in pairs:
   node=copy.deepcopy(oldmodes[oldmode]);node.set('name',newmode);leaf=node.find('pb_type');assert leaf.get('blif_model')=='.subckt '+old;leaf.set('blif_model','.subckt '+new);pb.append(node);locations.append((pb,node))
 assert len(added)==2 and len(locations)==6;p=D/'architecture.xml';ET.ElementTree(root).write(p,encoding='unicode')
 for node in added:models.remove(node)
 for pb,node in locations:pb.remove(node)
 assert ET.tostring(root)==original
 result={'status':'DIRECT_PN_ARCH_CANDIDATE_ADDITIONS_ONLY_VERIFIED','new_models':['$_DFF_PN0_','$_DFF_PN1_'],'new_storage_modes':6,'existing_architecture_semantics_unchanged_after_removing_additions':True,'reset_timing_characterized':False,'native_labels_generated':False,'bindings':{str(q):sha(q) for q in [Path(__file__),source,D/'protocol.json',p,net]},'scope':'Model ports and3-site PN storage modes only. Exact negative reset functional semantics remain those of pinned simcells, outside architecture timing schema. No PP inversion candidate used.'};(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PRINCE_DIRECT_PN_ARCH_CREATED',6)
if __name__=='__main__':main()
