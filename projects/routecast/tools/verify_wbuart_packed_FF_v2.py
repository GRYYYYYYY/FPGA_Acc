"""Every ordinary FF and public packed interface, no routing/heldout claim."""
import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 pack=R/'experiments/wbuart_pack_v1_2026-10-20';rp=pack/'receipt.json';r=json.loads(rp.read_text());assert r['status']=='pack_success_pending_full_FF_pin_audit' and r['exit_code']==0
 for mapping in [r['bindings'],r['files']]:
  for p,h in mapping.items():assert sha(p)==h
 front=R/'experiments/wbuart_boolean_cut_keepdc_v1_2026-10-20';jp=front/'flat.json';compileproof=R/'experiments/wbuart_boolean_cut_keepdc_v1_2026-10-20/verification.json';cv=json.loads(compileproof.read_text());assert cv['bindings']['flat.json']==sha(jp)
 out=R/'experiments/wbuart_packed_FF_v2_2026-10-20';out.mkdir(exist_ok=False);helper=R/'tools/audit_external_packed_ordinary_FF_v2_2026_10_18.py';command=[sys.executable,str(helper),str(pack),str(rp),str(jp),'wbuart',str(out/'audit')]
 with (out/'protocol.json').open('x') as f:json.dump(dict(command=command,bindings={str(p):sha(p) for p in [Path(__file__),helper,rp,jp,compileproof]},scope='All599ordinary FF identities and D/clock/Q bits plus complete public packed ports. No async primitives expected. Not full HDL/four-state/packed-LUT equivalence, placement, route labels or strict-family assignment.'),f,indent=2)
 with (out/'audit.log').open('x') as log:code=subprocess.call(command,cwd=R,stdout=log,stderr=subprocess.STDOUT)
 assert code==0;ap=out/'audit/ordinary_FF_signal_verification_v2.json';a=json.loads(ap.read_text());assert a['ordinary_FF_count']==cv['FF_bits']==599 and not a['asynchronous_primitives_present'] and not a['primitive_counts'] and a['all_ordinary_FF_names_and_nonopen_D_clk_Q_pins_match_original_bits']
 for p,h in a['bindings'].items():assert sha(p)==h
 root=ET.parse(pack/'design.net').getroot();arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';assert root.get('architecture_id')=='SHA256:'+sha(arch) and root.get('atom_netlist_id')=='SHA256:'+sha(pack/'design.blif')
 lines=[];acc=''
 for raw in (pack/'design.blif').read_text().splitlines():
  value=raw.strip()
  if not value or value.startswith('#'):continue
  if value.endswith('\\'):acc+=value[:-1]+' ';continue
  lines.append((acc+value).split());acc=''
 assert not acc;inputs=next(x[1:] for x in lines if x[0]=='.inputs');outputs=next(x[1:] for x in lines if x[0]=='.outputs');nativeinputs=root.findtext('inputs','').split();nativeoutputs=root.findtext('outputs','').split();clocks=root.findtext('clocks','').split();assert len(inputs)==45 and len(nativeinputs)==44 and set(inputs)-set(nativeinputs)=={'i_wb_data[31]'} and not set(nativeinputs)-set(inputs)
 m=json.loads(jp.read_text())['modules']['wbuart'];unused_bit=m['ports']['i_wb_data']['bits'][31];assert not any(unused_bit in bits for c in m['cells'].values() for pin,bits in c['connections'].items() if c['port_directions'][pin]=='input');assert not any(unused_bit in p['bits'] for p in m['ports'].values() if p['direction']=='output')
 assert not any('i_wb_data[31]' in x[1:] for x in lines if x[0] in ['.names','.latch','.outputs'])
 assert set(nativeoutputs)=={'out:'+x for x in outputs} and len(nativeoutputs)==len(outputs)==40;assert clocks==['i_clk']
 bindings=dict(a['bindings'])
 for p in [Path(__file__),rp,compileproof,ap,pack/'design.net',arch,out/'protocol.json',out/'audit.log']:bindings[str(p)]=sha(p)
 with (out/'verification.json').open('x') as f:json.dump(dict(status='all599_packed_FF_bits_and_active_public_ports_verified_one_unused_PI_removed',bindings=bindings,FF_bits=599,all_FF_D_clock_Q_bits_equal_frozen_JSON=True,primary_input_bits=45,packed_primary_input_bits=44,proven_unused_removed_inputs=['i_wb_data[31]'],primary_output_bits=40,clock='i_clk',strict_unseen_admitted=False,new_placement_route_jobs=False,full_HDL_four_state_equivalence=False,scope='Exact lowered/mapped state boundary and native packed pin resolution, architecture/netlist hashes and complete active public IO with sole unused input i_wb_data[31] removed, independently checked to have no JSON cell-input/output or BLIF use. No full packed LUT functional/timing or original HDL certificate, placement/native-route target labels or strict-family admission.'),f,indent=2)
 print('PACKED FF/PORT ADMISSION PASS',599,44,40,flush=True)
if __name__=='__main__':main()
