"""Native utility masks, explicit unused-input convention and reference slice."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/prospective_external_family_native_LUT_masks_v1_2026-10-19';br=read(out/'build_receipt.json');binary=out/'native_LUT_mask';assert br['exit_code']==0 and sha(binary)==br['binary_sha256'];bp=read(out/'build_protocol.json');assert all(sha(p)==h for p,h in bp['bindings'].items());refroot=R/'experiments/prospective_external_family_LUT_reference_v1_2026-10-19';rv=read(refroot/'verification.json');assert all(sha(p)==h for p,h in rv['bindings'].items());refpath=refroot/'derived_physical_LUTs.jsonl';refs={r['atom']:r for r in map(json.loads,refpath.open())};blif=R/'experiments/prospective_external_family_pack_v1_2026-10-18/design.blif';atoms={};current=None;pending=''
 for raw in blif.read_text().splitlines():
  line=raw.split('#',1)[0].strip()
  if not line:continue
  if line.endswith('\\'):pending+=line[:-1]+' ';continue
  t=(pending+line).split();pending=''
  if t[0].startswith('.'):
   current=None
   if t[0]=='.names':current=t[-1];atoms[current]=dict(inputs=t[1:-1],cubes=[])
  elif current is not None:atoms[current]['cubes'].append(t)
 assert set(atoms)==set(refs) and len(refs)==6483;inputpath=out/'native_input.txt'
 with inputpath.open('x') as f:
  f.write(str(len(atoms))+'\n')
  for name,a in atoms.items():
   rot=refs[name]['physical_to_logical'];assert a['inputs']==refs[name]['logical_inputs'];n=len(a['inputs']);f.write(f'{name} {n} {len(rot)} {len(a["cubes"])}\n');f.write(' '.join(str(rot.index(str(j))) for j in range(n))+'\n')
   for pattern,value in a['cubes']:f.write(pattern+' '+value+'\n')
 protocol=dict(command=[str(binary)],bindings={str(p):sha(p) for p in [out/'build_receipt.json',out/'build_protocol.json',binary,refroot/'verification.json',refpath,blif,inputpath,Path(__file__).resolve()]},comparison='Native complete mask versus independently evaluated cubes permuted with unused physical inputs constrained0. Derived open-invariant reference compared on unused-input0 slice only. Record full-mask differences separately; no convention change based on outcome.',scope='Existing VPR static-library mask utility harness; packed permutation remains inherited from independent pin audit. Not native packed-state simulation or full HDL equivalence.')
 (out/'check_protocol.json').write_text(json.dumps(protocol,indent=2));native=out/'native_masks.txt'
 with inputpath.open() as inp,native.open('x') as log,(out/'native_stderr.log').open('x') as err:result=subprocess.run([str(binary)],stdin=inp,stdout=log,stderr=err)
 assert result.returncode==0;observed={};fullrows=0;slicerows=0;differences=0;affected=0
 for line in native.open():
  name,logical,physical=line.split();assert name in refs and name not in observed;observed[name]=True;r=refs[name];a=atoms[name];rot=r['physical_to_logical'];assert logical==r['logical_truth'] and len(physical)==1<<len(rot);values={int(v) for _,v in a['cubes']};assert len(values)==1;val=values.pop();diff=0
  for assignment,nativebit in enumerate(physical):
   openszero=all(not((assignment>>i)&1) for i,j in enumerate(rot) if j=='open');matched=openszero and any(all(c=='-' or int(c)==((assignment>>rot.index(str(j)))&1) for j,c in enumerate(pattern)) for pattern,_ in a['cubes']);expected=val if matched else 1-val;assert int(nativebit)==expected;fullrows+=1
   if openszero:assert nativebit==r['derived_physical_truth'][assignment];slicerows+=1
   elif nativebit!=r['derived_physical_truth'][assignment]:diff+=1
  differences+=diff;affected+=diff>0
 assert set(observed)==set(refs)
 with (out/'verification.json').open('x') as f:json.dump(dict(status='ALL6483_NATIVE_LIBRARY_LOGICAL_MASKS_AND_PADDED_PHYSICAL_MASKS_VERIFIED',exit_code=result.returncode,LUT_atoms=len(observed),native_physical_rows_verified=fullrows,connected_assignment_reference_rows_verified=slicerows,outside_zero_padding_domain_differences=differences,LUTs_with_outside_domain_differences=affected,bindings={str(p):sha(p) for p in [out/'check_protocol.json',native,out/'native_stderr.log']},scope=protocol['scope'],unused_input_scope='Full native masks checked under native zero-padding cube convention. Open-invariant derived reference agrees on all unused-input0 assignments; differences outside slice are documented, not a native bug or proof of actual tied-pin behavior.'),f,indent=2)
 print('NATIVE_LIBRARY_LUT_MASKS_PASS',len(observed),'full',fullrows,'slice',slicerows,'outside differences',differences)
if __name__=='__main__':main()
