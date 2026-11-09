"""Independent four-value sampled-event and complete transformed-pin audit."""
import itertools,json,re,xml.etree.ElementTree as ET
from pathlib import Path
from verify_external_family_cut_v1_2026_10_18 import lines
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_reset_polarity_v1_2026-10-20';D=E/'prince_reset_polarity_verification_v1_2026-10-20'
def main():
 receipt=json.loads((S/'receipt.json').read_text());assert all(sha(p)==h for p,h in receipt['bindings'].items());sim=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/share/yosys/simcells.v';text=sim.read_text();fragments={}
 for polarity,edge,reset_active in [('N','negedge','0'),('P','posedge','1')]:
  for bit in [0,1]:
   name='$_DFF_P'+polarity+str(bit)+'_';match=re.search(r'module\s+\\'+re.escape(name)+r'\s+\(.*?endmodule',text,re.S);assert match;fragment=match.group();compact=re.sub(r'\s+','',fragment);assert 'always@(posedgeCor'+edge+'R)beginif(R=='+reset_active+')Q<='+str(bit)+';elseQ<=D;end' in compact;fragments[name]=fragment
 invert={'0':'1','1':'0','x':'x','z':'x'};positive={('0','1'),('0','x'),('0','z'),('x','1'),('z','1')};negative={('1','0'),('1','x'),('1','z'),('x','0'),('z','0')};transitions=0
 for c0,c1,r0,r1,d,q,bit in itertools.product('01xz','01xz','01xz','01xz','01xz','01xz',[0,1]):
  clock_event=(c0,c1) in positive;pn_event=clock_event or (r0,r1) in negative;pp_event=clock_event or (invert[r0],invert[r1]) in positive;assert pn_event==pp_event
  direct=(str(bit) if r1=='0' else d) if pn_event else q
  normalized=(str(bit) if invert[r1]=='1' else d) if pp_event else q
  assert direct==normalized;transitions+=1
 original=lines(E/'prince_compile_cut_v2_2026-10-20/design.blif');normalized=lines(S/'design.blif');oldcells=[r for r in original if r[0]=='.subckt'];newcells=[r for r in normalized if r[0]=='.subckt'];assert len(oldcells)==len(newcells)==646
 for a,b in zip(oldcells,newcells):
  assert b[1]=={'$_DFF_PN0_':'$_DFF_PP0_','$_DFF_PN1_':'$_DFF_PP1_'}[a[1]];p=dict(x.split('=',1) for x in a[2:]);n=dict(x.split('=',1) for x in b[2:]);assert {k:p[k] for k in ['C','D','Q']}=={k:n[k] for k in ['C','D','Q']} and p['R']=='reset_n' and n['R']=='routecast_prince_reset_high_v1'
 def logic(rows):return [r for r in rows if r[0]!='.subckt']
 a,b=logic(original),logic(normalized);index=b.index(['.names','reset_n','routecast_prince_reset_high_v1']);assert b[index+1]==['0','1'];assert b[:index]+b[index+2:]==a
 arch=E/'async_reset_arch_candidate_v2_2026-10-08/architecture.xml';root=ET.parse(arch).getroot();models={m.get('name'):m for m in root.findall('./models/model')}
 for model in ['$_DFF_PP0_','$_DFF_PP1_']:
  assert model in models;assert {p.get('name') for p in models[model].findall('./input_ports/port')}=={'C','D','R'} and {p.get('name') for p in models[model].findall('./output_ports/port')}=={'Q'};assert sum(p.get('blif_model')=='.subckt '+model for p in root.iter('pb_type'))==3
 D.mkdir(exist_ok=False);files=[Path(__file__),S/'receipt.json',S/'design.blif',E/'prince_compile_cut_v2_2026-10-20/design.blif',sim,arch,E/'async_reset_arch_candidate_v2_2026-10-08/receipt.json'];v={'status':'PASS_SAMPLED_FOUR_VALUE_EVENT_ABSTRACTION_AND_ALL646_NORMALIZED_PINS','sampled_event_transitions':transitions,'state_cell_pin_records':646,'added_LUT_inverters':1,'four_primitive_definitions_bound':fragments,'experimental_PP_architecture_model_ports_and_pb_mappings_checked':True,'strict_unseen_admitted':False,'native_packing_admitted':False,'full_HDL_delta_cycle_equivalence':False,'new_native_labels':False,'bindings':{str(p):sha(p) for p in files},'scope':'Atomic sampled clock/reset event model with4-valued signals and exact C/D/Q pin/state constants. Does not establish simulator delta-cycle races, physical inverter/reset delay or recovery/removal constraints, full RTL lowering equivalence or original architecture support. No reset deassert/clock separation assumption admitted for labels. Full original netlist remains immutable.'};(D/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print('PRINCE_POLARITY_AUDIT_PASS',transitions,646)
if __name__=='__main__':main()
