"""Explicit native-loaded LUT functional export; separate open-X and ground trials."""
import json,hashlib,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def esc(s):return '\\'+s+' '
def main():
 o=E/'prince_loaded_packing_sim_v1_2026-10-20';o.mkdir(exist_ok=False)
 native=E/'prince_native_packed_LUTs_v1_2026-10-20';proof=native/'verification.json';d=json.loads(proof.read_text())
 for p,h in d['bindings'].items():assert sha(p)==h
 blif=E/'prince_direct_pn_pack_v1_2026-10-20/design.blif';lines=[s.split() for s in blif.read_text().splitlines() if s.strip() and not s.startswith('#')];inputs=next(t[1:] for t in lines if t[0]=='.inputs');outputs=next(t[1:] for t in lines if t[0]=='.outputs');ffs=[t for t in lines if t[0]=='.subckt'];assert len(ffs)==646 and all(t[1] in ['$_DFF_PN0_','$_DFF_PN1_'] for t in ffs)
 loaded=[s.rstrip('\n').split('\t') for s in (native/'loaded_LUTs.tsv').open()];assert len(loaded)==2096
 signals=set(inputs+outputs)
 for name,w,pins,mask in loaded:signals.add(name);signals.update(s for s in pins.split(',') if s!='open')
 for t in ffs:signals.update(s.split('=',1)[1] for s in t[2:])
 old=E/'prince_mapped_differential_v2_2026-10-20';harness=(old/'harness.sv').read_text().replace('mapped_prince','packed_prince');(o/'harness.sv').write_text(harness)
 simproof=E/'prince_LUT_fourstate_v1_2026-10-20/receipt.json';assert json.loads(simproof.read_text())['passed']
 functional=E/'prince_LUT_fourstate_v1_2026-10-20/LUT_K_functional_only.v';tool=Path(json.loads((E/'prospective_external_family_source_v2_2026-10-18/source_verification.json').read_text())['yosys_path']);cells=tool.parent.parent/'share/yosys/simcells.v'
 usr=E/'prospective_external_family_sim_runtime_v1_2026-10-18/root/usr';iv=usr/'bin/iverilog';vvp=usr/'bin/vvp';lib=usr/'lib/x86_64-linux-gnu/ivl';s=E/'prince_candidate_source_v2_2026-10-20/upstream/src/rtl';rtl=[s/'prince.v',s/'prince_core.v'];tb=E/'prince_upstream_testbench_source_v1_2026-10-20/tb_prince.v'
 paths=[Path(__file__),proof,simproof,native/'loaded_LUTs.tsv',blif,old/'harness.sv',functional,cells,iv,vvp,*rtl,s/'prince_round_functions.vh',tb];bindings={str(p):sha(p) for p in paths}
 protocol={'bindings':bindings,'contracts':['unconnected_X','explicit_ground'],'LUT_atoms':len(loaded),'async_FFs':len(ffs),'scope':'Owned functional export of captured native loaded LUT masks and signal identities, with exact original BLIF PN FF models from pinned simcells. Not VPR default writer output, no interconnect timing, reachability/formal/unseen claim. Source upstream tb unchanged; same settled clock sampling as previous mapped study. Ground is explicit separate policy, not default X equivalence.'}
 (o/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
 for policy,value in [('unconnected_X',"1'bx"),('explicit_ground',"1'b0")]:
  q=o/policy;q.mkdir();design=q/'packed.v'
  with design.open('x') as f:
   f.write('module packed_prince('+','.join(map(esc,inputs+outputs))+');\n')
   for direction,ports in [('input',inputs),('output',outputs)]:
    for port in ports:f.write(direction+' '+esc(port)+';\n')
   for name in sorted(signals-set(inputs+outputs)):f.write('wire '+esc(name)+';\n')
   for k,(name,w,pins,mask) in enumerate(loaded):
    pins=pins.split(',');assert len(pins)==int(w) and len(mask)==1<<int(w)
    expr=','.join(value if p=='open' else esc(p) for p in reversed(pins))
    f.write(f"LUT_K #(.K({w}),.LUT_MASK({len(mask)}'b{mask[::-1]})) lut{k}(.in({{{expr}}}),.out({esc(name)}));\n")
   for k,t in enumerate(ffs):
    ports=[a.split('=',1) for a in t[2:]];assert {a for a,b in ports}=={'C','D','Q','R'}
    f.write(esc(t[1])+f'ff{k}('+','.join('.'+a+'('+esc(b)+')' for a,b in ports)+');\n')
   f.write('endmodule\n')
  cmd=[str(iv),'-B',str(lib),'-g2012','-I',str(s),'-s','differential','-o',str(q/'sim.vvp'),*map(str,rtl),str(tb),str(functional),str(cells),str(design),str(o/'harness.sv')]
  with (q/'compile.log').open('x') as log:rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=q)
  assert rc==0,'compile log retained'
  with (q/'simulation.log').open('x') as log:rc=subprocess.call([str(vvp),'-M',str(lib),str(q/'sim.vvp')],stdout=log,stderr=subprocess.STDOUT,cwd=q)
  text=(q/'simulation.log').read_text();matches=re.findall(r'STRICT_DIFFERENTIAL_CHECKS (\d+)',text);checks=int(matches[-1]) if matches else 0;passed=rc==0 and checks>0 and 'All 09 test cases completed successfully' in text and 'DIFFERENTIAL_FAIL' not in text
  results.append(dict(policy=policy,exit_code=rc,passed=passed,samples=checks,compile_command=cmd,files={str(p):sha(p) for p in q.iterdir() if p.is_file()}));print(policy,rc,passed,checks,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 (o/'receipt.json').write_text(json.dumps(dict(results=results,bindings=bindings,scope=protocol['scope']),indent=2)+'\n')
if __name__=='__main__':main()
