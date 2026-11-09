"""Compare native loaded atom/pb-route state to independently resolved XML pins."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 root=R/'experiments/prospective_external_family_native_packed_LUTs_v1_2026-10-19';receipt=read(root/'receipt.json');assert receipt['exit_code']==0;protocol=read(root/'protocol.json')
 for d in [receipt,protocol]:
  for p,h in d['bindings'].items():assert sha(p)==h
 export=root/'loaded_LUTs.tsv';assert sha(export)==receipt['export_sha256'];referencep=R/'experiments/prospective_external_family_LUT_reference_v1_2026-10-19/derived_physical_LUTs.jsonl';refs={r['atom']:r for r in map(json.loads,referencep.open())};nativep=R/'experiments/prospective_external_family_native_LUT_masks_v1_2026-10-19/native_masks.txt';old={t[0]:t[2] for t in map(str.split,nativep.open())};seen=set();rows=0;slicerows=0;openpins=0
 for line in export.open():
  name,width,signals,mask=line.rstrip('\n').split('\t');width=int(width);signals=signals.split(',');assert name in refs and name not in seen;seen.add(name);r=refs[name];rot=r['physical_to_logical'];assert len(rot)==width==len(signals) and mask==old[name] and len(mask)==1<<width
  for i,j in enumerate(rot):assert signals[i]==('open' if j=='open' else r['logical_inputs'][int(j)])
  for assignment,bit in enumerate(mask):
   if all(not((assignment>>i)&1) for i,j in enumerate(rot) if j=='open'):assert bit==r['derived_physical_truth'][assignment];slicerows+=1
  openpins+=sum(s=='open' for s in signals);rows+=len(mask)
 assert seen==set(refs)==set(old) and len(seen)==6483 and slicerows==184360
 for p,h in protocol['bindings'].items():assert sha(p)==h
 vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/base';paths=[root/'receipt.json',root/'protocol.json',export,referencep,nativep,Path(__file__).resolve(),vendor/'netlist_writer.cpp',vendor/'read_options.cpp'];bindings={str(p):sha(p) for p in paths}
 with (root/'verification.json').open('x') as f:json.dump(dict(status='ALL6483_NATIVE_LOADED_PACKED_LUT_INPUT_NETS_AND_MASKS_MATCH_XML_REFERENCE',LUT_atoms=len(seen),physical_mask_rows=rows,zero_unused_reference_rows=slicerows,open_physical_input_pins=openpins,bindings=bindings,scope='Masks and physical net identities derived directly from native vpr_load_packing state, no supplied external rotation in loader. Matches independent XML hierarchy/rotation audit and original native helper. No new pack/place/route execution. No post-synthesis whole-circuit simulation or physical timing claim.',writer_convention='Pinned read_options default --post_synth_netlist_unconn_inputs=unconnected; netlist_writer emits X for unconnected. Explicit gnd emits0. Loader never calls writer. Zero-unused slice agreement must not be presented as default post-synthesis whole-circuit equivalence.',strict_unseen_admitted=False),f,indent=2)
 print('NATIVE_LOADED_PACKED_LUT_CHECK_PASS',len(seen),rows,slicerows,'openpins',openpins)
if __name__=='__main__':main()
