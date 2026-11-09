"""Test source-derived native DP specialization with physically tied-off we2."""
import hashlib
import json
import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'native_ram_singlewrite_specialization_v1_2026-10-09'; D.mkdir(exist_ok=False)
source=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/primitives.v'
wrapper=E/'delayed_write_ram_rtl_v2_2026-10-09/wrapper.v'
receipt=json.loads((wrapper.parent/'receipt.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(wrapper)==receipt['files'][str(wrapper)]
y=Path(next(p for p in receipt['bindings'] if p.endswith('/bin/yosys')))
assert sha(y)==receipt['bindings'][str(y)]
t=source.read_text(); begin=t.index('module dual_port_ram #(')
primitive=t[begin:t.index('endmodule',begin)+len('endmodule')]
branch='''        if(we2) begin
            Mem[addr2] = data2;
        end'''
assert primitive.count(branch)==1
specialized=primitive.replace(branch,'        // we2 is fixed to zero at every use: no port-2 write.')
(D/'original_primitive.v').write_text(primitive+'\n')
(D/'specialized_primitive.v').write_text(specialized+'\n')
rtl=wrapper.read_text(); assert ".we2(1'b0)" in rtl
(D/'wrapper.v').write_text(rtl)
script='read_verilog specialized_primitive.v wrapper.v\nhierarchy -check -top miter\nproc\nsetattr -mod -unset keep_hierarchy\nsetattr -unset keep_hierarchy\nflatten\nmemory_map\nopt\ncheck -assert\nsat -seq 6 -set-init-zero -prove bad 0 -show golden -show actual\n'
(D/'check.ys').write_text(script)
bindings={str(p):sha(p) for p in [Path(__file__),source,wrapper,y,*D.iterdir()] if p.is_file()}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,timeout_s=60,
    scope='Source-derived DP behavioral model removes only second write branch under actual constant we2=0, retaining both blocking posedge read processes. Small 2-bit four-word bounded six-timepoint diagnostic, matched zero state. Not original general DP equivalence, simulator scheduling proof, physical macro characterization or Full admission.'),indent=2)+'\n')
with (D/'check.log').open('x') as log:
    try:code=subprocess.run([str(y),'-s','check.ys'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
    except subprocess.TimeoutExpired:code='TIMEOUT'
log=(D/'check.log').read_text()
out=dict(exit_code=code,passed=code==0 and 'no model found: SUCCESS' in log,
    driver_conflicts_present='driver-driver conflict' in log,bindings=bindings,
    admitted_for_prediction=False,files={str(p):sha(p) for p in D.iterdir() if p.is_file()})
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['exit_code','passed','driver_conflicts_present']}))
