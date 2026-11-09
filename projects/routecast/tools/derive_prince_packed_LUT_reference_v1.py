"""Derived reference masks, not captured native packed LUT configuration."""
import json,itertools
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/prince_LUT_reference_v1_2026-10-20';out.mkdir(exist_ok=False);proof=R/'experiments/prince_packed_LUT_pins_v1_2026-10-20/verification.json';v=read(proof);assert v['LUT_atoms']==2096
 for p,h in v['bindings'].items():assert sha(p)==h
 blif=R/'experiments/prince_direct_pn_pack_v1_2026-10-20/design.blif';atoms={};pending='';current=None
 for raw in blif.read_text().splitlines():
  line=raw.split('#',1)[0].strip()
  if not line:continue
  if line.endswith('\\'):pending+=line[:-1]+' ';continue
  tokens=(pending+line).split();pending=''
  if tokens[0].startswith('.'):
   current=None
   if tokens[0]=='.names':current=tokens[-1];assert current not in atoms;atoms[current]=dict(inputs=tokens[1:-1],cubes=[])
  elif current is not None:atoms[current]['cubes'].append(tokens)
 assert not pending and set(atoms)==set(v['atoms']);rows=0;off=0;unusedchecks=0;path=out/'derived_physical_LUTs.jsonl'
 with path.open('x') as f:
  for name,a in atoms.items():
   mapping=v['atoms'][name];assert a['inputs']==mapping['inputs'];rotation=mapping['physical_to_logical'];n=len(a['inputs']);width=len(rotation);assert width in (5,6) and n<=width;assert a['cubes'] and all(len(t)==2 and len(t[0])==n and set(t[0])<=set('01-') and t[1] in ('0','1') for t in a['cubes']);polarity={int(t[1]) for t in a['cubes']};assert len(polarity)==1;value=polarity.pop();off+=value==0
   # First evaluation expands logical cubes to complete integer assignments.
   mask=[1-value]*(1<<n)
   for pattern,_ in a['cubes']:
    for bits in itertools.product(*[(0,1) if c=='-' else (int(c),) for c in pattern]):mask[sum(bit<<i for i,bit in enumerate(bits))]=value
   physical=[]
   for assignment in range(1<<width):
    logical=0
    for i,j in enumerate(rotation):
     if j!='open':logical|=((assignment>>i)&1)<<int(j)
    physical.append(mask[logical])
    # Independent direct matching permutes cubes onto physical pin positions.
    matched=any(all(c=='-' or int(c)==((assignment>>rotation.index(str(j)))&1) for j,c in enumerate(pattern)) for pattern,_ in a['cubes']);direct=value if matched else 1-value;assert physical[-1]==direct;rows+=1
   for i,j in enumerate(rotation):
    if j=='open':
     for assignment in range(1<<width):assert physical[assignment]==physical[assignment^(1<<i)];unusedchecks+=1
   f.write(json.dumps(dict(atom=name,logical_inputs=a['inputs'],physical_to_logical=rotation,indexing='physical pin0 is least significant assignment bit; string entry index is assignment integer',derived_physical_truth=''.join(map(str,physical)),logical_truth=''.join(map(str,mask))),separators=(',',':'))+'\n')
 vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/base';sources=[vendor/'atom_netlist_utils.cpp',vendor/'netlist_writer.cpp'];bindings={str(p):sha(p) for p in [proof,blif,path,Path(__file__).resolve(),*sources]}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='ALL2096_DERIVED_LUT_REFERENCE_MASKS_EXHAUSTIVELY_ROTATION_CHECKED',LUT_atoms=len(atoms),physical_assignments_checked=rows,off_set_encoded_LUTs=off,open_pin_invariance_checks=unusedchecks,bindings=bindings,scope='BLIF plus previously verified packed rotations defines this derived reference. Cube expansion versus direct permuted matching and open-pin invariance checked. NOT independently captured native masks, native packed simulation, full HDL/four-state/timing proof, unseen-family admission or routing-label evidence.'),f,indent=2)
 print('DERIVED_LUT_REFERENCE_PASS',len(atoms),rows,'off-set LUTs',off,'open-pin checks',unusedchecks)
if __name__=='__main__':main()
