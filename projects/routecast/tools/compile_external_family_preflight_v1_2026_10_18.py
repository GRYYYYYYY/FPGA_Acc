"""Isolated compile readiness only; no family assignment or physical labels."""
import hashlib,json,os,subprocess,time,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=R/'experiments/prospective_external_family_source_v2_2026-10-18';vp=source/'source_verification.json';v=json.loads(vp.read_text());runtime=R/'experiments/prospective_external_family_runtime_v1_2026-10-18';rp=runtime/'verification.json';rt=json.loads(rp.read_text());assert rt['hierarchy_exit_status']==0
 out=R/'experiments/prospective_external_family_compile_preflight_v1_2026-10-18';out.mkdir(exist_ok=False);tool=Path(v['yosys_path']);build=tool.parents[1];abc=build/'abc/abc';share=build/'share/yosys';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';assert abc.is_file() and (share/'techmap.v').is_file()
 widths={int(i.get('num_pins')) for e in ET.parse(arch).getroot().iter('pb_type') if e.get('blif_model')=='.names' for i in e.findall('input')};assert 6 in widths
 rtl=[Path(a['path']) for a in v['assets'] if a['relative'] in v['RTL_compilation_units']]
 for a in v['assets']:assert sha(a['path'])==a['sha256']
 paths=[vp,rp,tool,abc,arch,*rtl,Path(__file__)]+[p for p in share.rglob('*') if p.is_file()];bindings={str(p):sha(p) for p in paths}
 commands=['read_verilog '+' '.join('"'+str(p)+'"' for p in rtl),'hierarchy -check -top chacha','proc','flatten','memory_map','opt','techmap -map "'+str(share/'techmap.v')+'"','opt','dffunmap','abc -exe "'+str(abc)+'" -lut 6','opt_clean','check -assert','write_json "'+str(out/'mapped.json')+'"','write_blif "'+str(out/'mapped.blif')+'"']
 with (out/'commands.ys').open('x') as f:f.write('\n'.join(commands)+'\n')
 protocol=dict(bindings=bindings,commands=commands,top='chacha',LUT_inputs=6,scope='Compile-to-LUT/DFF readiness under the existing architecture LUT limit; no source changes, clock/reset rewriting, placement, routing, new target labels or strict family admission. Mapped outputs require independent primitive/FF and equivalence audit before physical use.',strict_unseen_admitted=False)
 with (out/'protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
 env=os.environ.copy();lib=runtime/'tcl-root/usr/lib/x86_64-linux-gnu';env['LD_LIBRARY_PATH']=str(lib)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');tick=time.perf_counter()
 with (out/'frontend.log').open('x') as log:code=subprocess.call([str(tool),'-Q','-T','-s',str(out/'commands.ys')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
 elapsed=time.perf_counter()-tick
 for p,h in bindings.items():assert sha(p)==h
 types={}
 if code==0:
  mapped=json.loads((out/'mapped.json').read_text());assert list(mapped['modules'])==['chacha'];types=dict(Counter(c['type'] for c in mapped['modules']['chacha']['cells'].values()))
 files={str(p):sha(p) for p in out.iterdir() if p.is_file()}
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='mapped_compile_outputs_pending_independent_audit' if code==0 else 'compile_preflight_failed',bindings=bindings,files=files,exit_status=code,component_seconds=elapsed,mapped_cell_types=types,strict_unseen_admitted=False,new_native_labels_read=False,new_placement_or_route_jobs=False,scope=protocol['scope']),f,indent=2)
 print('COMPILE PREFLIGHT EXIT',code,'CELL TYPES',types,flush=True)
 if code:raise SystemExit(code)
if __name__=='__main__':main()
