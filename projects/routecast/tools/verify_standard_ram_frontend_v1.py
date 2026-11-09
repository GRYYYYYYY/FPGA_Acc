"""Standard input flag, retained storage and paired trace proof evidence audit."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'preroute_family_admission_v1_2026-10-20';D=E/'ram_mapping_semantics_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def number(v):return int(v,2) if isinstance(v,str) else int(v)
def main():
 manifest=load(S/'structure_preflight_manifest_v5.json')
 for p,h in manifest['bindings'].items():assert sha(p)==h
 library=Path(manifest['primitive_library']);installed=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/share/yosys/parmys/vtr_primitives.v';assert installed.read_bytes()==library.read_bytes()
 standard=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/misc/yosys/synthesis.tcl';assert 'read_verilog -nomem2reg +/parmys/vtr_primitives.v' in standard.read_text()
 rows=[];bindings={str(p):sha(p) for p in [standard,library,installed,S/'structure_preflight_manifest_v5.json',D/'standard_memory_contract_v2/results.json',Path(__file__)]}
 for name in ['mcml','arm_core','mkDelayWorker32B']:
  folder=S/'structure_preflight_v5'/name;terminal=load(folder/'terminal.json');assert terminal['exit_code']==0;commands=(folder/'commands.ys').read_text();assert '-nomem2reg' in commands and '-lib ' not in commands and 'async2sync' not in commands and 'adff2dff' not in commands
  case=next(r for r in manifest['cases'] if r['name']==name);snapshot=folder/Path(case['source']).name;assert sha(snapshot)==case['source_sha256']==sha(case['source']);original=load(folder/'proc.json');collected=D/'standard_memory_contract_v2'/name/'collected.json';after=load(collected);before_bits=sum(v['width']*v['size'] for m in original['modules'].values() for v in m.get('memories',{}).values());mems=[c for m in after['modules'].values() for c in m.get('cells',{}).values() if c['type'] in ['$mem','$mem_v2']];after_bits=sum(number(c['parameters']['WIDTH'])*number(c['parameters']['SIZE']) for c in mems);assert before_bits==after_bits and before_bits>0
  assert {k:(p['direction'],len(p['bits'])) for k,p in original['modules'][name]['ports'].items()}=={k:(p['direction'],len(p['bits'])) for k,p in after['modules'][name]['ports'].items()}
  for module,obj in original['modules'].items():
   if module.endswith('\\dual_port_ram') or module.endswith('\\single_port_ram'):
    assert not number(obj.get('attributes',{}).get('blackbox',0));assert obj.get('memories')
    for port,p in obj['ports'].items():
     if port.startswith('out'):assert all(isinstance(b,int) for b in p['bits'])
  capture=next(r for r in load(D/'standard_memory_contract_v2/results.json')['rows'] if r['name']==name);assert capture['exit_code']==0;rows.append(dict(name=name,definition_storage_bits=before_bits,collected_memory_definitions=len(mems),public_ports_preserved=True,functional_models_not_blackboxes=True))
  for p in [folder/'commands.ys',folder/'terminal.json',folder/'proc.json',collected]:bindings[str(p)]=sha(p)
 traces=load(D/'defined_trace_sat/results.json')['rows'];old,new=traces;assert old['exit_code']!=0 and old['proof_failed'] and new['exit_code']==0 and new['SAT_proof_success'];p=D/'defined_trace_sat/standard_nomem2reg/commands.ys';assert '-set-init' not in p.read_text();bindings[str(p)]=sha(p);bindings[str(D/'defined_trace_sat/results.json')]=sha(D/'defined_trace_sat/results.json')
 assert not list(D.rglob('*.route'))
 out=dict(status='STANDARD_NOMEM2REG_FRONTEND_STORAGE_AND_BOUNDED_TRACE_VERIFIED',rows=rows,paired_trace_old_failed_standard_passed=True,zero_initialization_assumed=False,scope='Raw frontend/storage-preservation and one bounded defined-input RTLILtrace only. Fullsize/alltraces/fullHDLfourstate,collisionhardware/nativepacking/STA/heldout remainunproven. Fullcollected graph,including surrounding bypass/mux/FFlogic,is authoritative;memory masks alone not the whole primitivebehavior.',original_full9_gate=False,bindings=bindings)
 with (D/'standard_frontend_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status']);print(rows)
if __name__=='__main__':main()
