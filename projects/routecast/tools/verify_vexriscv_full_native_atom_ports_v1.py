"""Authenticate native original/cleaned atom top port identities and sweep difference."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_full_native_sdc_echo_v1_2026-10-09';D=E/'vexriscv_full_native_atom_ports_v1_2026-10-09';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();r=json.loads((B/'receipt.json').read_text());assert r['exit_code']==0
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
def ports(p):
 lines=[];pending=[]
 for raw in p.read_text().splitlines():
  w=raw.split()
  if not w or w[0].startswith('#'):continue
  continued=w[-1]==chr(92);pending.extend(w[:-1] if continued else w)
  if not continued:lines.append(pending);pending=[]
 assert not pending
 ins=[w[1:] for w in lines if w[0]=='.inputs'];outs=[w[1:] for w in lines if w[0]=='.outputs'];assert ins and outs
 return set(ins[0]),set(outs[0])
source=ports(B/'design.blif');original=ports(B/'atom_netlist.orig.echo.blif');cleaned=ports(B/'atom_netlist.cleaned.echo.blif');assert source==original
removed=source[0]-cleaned[0];assert removed=={'dBus_rsp_payload_last','debug_bus_cmd_payload_address[0]','debug_bus_cmd_payload_address[1]'}
assert cleaned[0]<=source[0] and cleaned[1]==source[1] and 'clk' in cleaned[0];assert len(cleaned[0])==116 and len(cleaned[1])==145
D.mkdir(exist_ok=False);report=dict(bindings={str(p):sha(p) for p in (Path(__file__).resolve(),B/'receipt.json',B/'design.blif',B/'atom_netlist.orig.echo.blif',B/'atom_netlist.cleaned.echo.blif')},original_input_count=119,cleaned_input_count=116,output_count=145,removed_inputs=sorted(removed),original_native_ports_exact=True,cleaned_outputs_exact=True,timing_constraints_echo_exists=(B/'timing_constraints.echo').exists(),scope='Native atom top port identity/sweep proof only. Exit-before-pack did not export timing constraint internals; not atom-pin timing coverage, packing, routing STA or prediction admission.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS original119/clean116 inputs and145 outputs; exact three removed')
