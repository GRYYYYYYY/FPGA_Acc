"""Freeze Ethernet candidate and routecast method before HDL synthesis; no native labels."""
import sys,json,time,subprocess,shutil,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
candidate=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/benchmarks/freecores/ethmac.v'
prior=subprocess.run(['rg','-l','-F','-e',sha(candidate),'-e','ethmac.v',str(R/'experiments'),str(R/'tools'),str(R/'RESEARCH_PLAN.md'),'--glob','protocol.json','--glob','receipt.json','--glob','*.py','--glob','*.md'],capture_output=True,text=True)
assert prior.returncode in [0,1]
shared=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';out=R/'experiments/ethernet_family_candidate_v1_2026-10-08';out.mkdir();tool=json.loads((R/'experiments/prospective_family_candidates_2026-10-06/frontend_availability.json').read_text());yosys=Path(tool['yosys_path']);assert sha(yosys)==tool['sha256'];bindings={**closure([Path(__file__),R/'tools/run_resident_soft_demand_affected_cache_v1.py']),str(yosys):sha(yosys)};cases=[]
(out/'prior_use_audit.json').write_text(json.dumps({'source_path':str(candidate),'source_sha256':sha(candidate),'search_command':prior.args,'exit_code':prior.returncode,'matches':prior.stdout.splitlines(),'scope':'Local explicit filename/hash references only; own preparation script included. Absence does not prove complete lineage or global unseen status.'},indent=2)+'\n')
for name,top in [('ethmac','eth_top')]:
 hdl=shared/'vtr_flow/benchmarks/freecores'/f'{name}.v';bindings[str(hdl)]=sha(hdl);w=out/name;w.mkdir();shutil.copyfile(hdl,w/'design.v');script=f'read_verilog design.v\nhierarchy -check -top {top}\nsynth -top {top} -flatten -lut 6\ndffunmap\ncheck -assert\nstat\nwrite_json design.json\nwrite_blif design.blif\n';(w/'synth.ys').write_text(script);bindings[str(w/'synth.ys')]=sha(w/'synth.ys');cases.append({'name':name,'top':top,'source':str(hdl),'command':[str(yosys),'-s','synth.ys']})
protocol={'bindings':bindings,'cases':cases,'family':'Ethernet MAC candidate; single available local family member','scope':'Prospective candidate family only; local prior-use audit pending. No native route labels read/generated. Existing method frozen: original positive RR/RC, original1ns-or-ceil1.5floor budgets, two50psfeedback rounds plus static50ps destination CHANspan; same wholeNET admission. All outcomes retained regardless frontend/route outcome, no weight retuning on future tests. LUT6 frontend candidate not yet equivalence/native or heldout generalization evidence.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for case in cases:
 name=case['name'];w=out/name;begin=time.perf_counter()
 try:
  with (w/'synthesis.log').open('w') as log:code=subprocess.run(case['command'],cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  blif=(w/'design.blif').read_text() if (w/'design.blif').exists() else '';row={'name':name,'exit_code':code,'seconds':time.perf_counter()-begin,'blif_subckts':re.findall(r'^\.subckt\s+(\S+)',blif,re.M),'latches':len(re.findall(r'^\.latch\s',blif,re.M)),'lut_names':len(re.findall(r'^\.names\s',blif,re.M))}
 except subprocess.TimeoutExpired:row={'name':name,'exit_code':'TIMEOUT','seconds':time.perf_counter()-begin}
 row['files']={str(f):sha(f) for f in w.iterdir() if f.is_file()};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,row['exit_code'],row.get('lut_names'),row.get('blif_subckts'),flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'bindings':bindings,'rows':rows,'frontend_only':True},indent=2)+'\n')
