"""Actual wrapper step under explicit abstract memory relation; not Full equivalence."""
import hashlib
import json
import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'emitted_ram_relational_step_v1_2026-10-09'; D.mkdir(exist_ok=False)
source=E/'full_ram_mapping_candidate_v1_2026-10-09/wrappers.v'
receipt=json.loads((source.parent/'receipt.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)==receipt['files'][str(source)]
y=Path(next(p for p in receipt['bindings'] if p.endswith('/bin/yosys')))
assert sha(y)==receipt['bindings'][str(y)]
t=source.read_text(); a=t.index('module rc_delayed_slice(')
slice_rtl=t[a:t.index('endmodule',a)+len('endmodule')]
# Expose pre-edge pending state and replace only macro read boundary with an oracle.
slice_rtl=slice_rtl.replace('output [19:0] q);','input [19:0] physical_read,input schedule,output prior_hit,output [19:0] prior_data,output [19:0] q);')
begin=slice_rtl.index('dual_port_ram #('); end=slice_rtl.index(';',begin)+1
slice_rtl=slice_rtl[:begin]+'''reg [19:0] oracle_raw;
assign raw=oracle_raw;
assign prior_hit=pw && pa==ra;
assign prior_data=pd;
always @(posedge clk) oracle_raw <= (schedule && prior_hit) ? pd : physical_read;
'''+slice_rtl[end:]
model='''
module miter(input clk,we,re,schedule,input [9:0] wa,ra,input [19:0] data,physical_read,
output bad,output reg [19:0] golden,output [19:0] actual);
wire hit; wire [19:0] pending;
rc_delayed_slice dut(.clk(clk),.we(we),.re(re),.wa(wa),.ra(ra),.data(data),
.physical_read(physical_read),.schedule(schedule),.prior_hit(hit),.prior_data(pending),.q(actual));
// Required pre-edge relation: logical read = apply_pending(physical memory, pending)[ra].
always @(posedge clk) if(re) golden <= hit ? pending : physical_read;
assign bad=golden!=actual;
endmodule
'''
script='read_verilog miter.v\nhierarchy -check -top miter\nproc\nflatten\nopt\ncheck -assert\nsat -seq 2 -set-at 1 bad 0 -prove bad 0 -show golden -show actual\n'
# Remove only pw/er init for arbitrary binary pre-edge wrapper state; actual init is audited separately.
slice_rtl=slice_rtl.replace('reg pw=0,er=0,hit;','reg pw,er,hit;')
(D/'miter.v').write_text(slice_rtl+model)
(D/'check.ys').write_text(script)
bindings={str(p):sha(p) for p in [Path(__file__),source,y,D/'miter.v',D/'check.ys']}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,timeout_s=60,
    scope='10-bit address, 20-bit data, arbitrary binary pre-edge registers with equal visible outputs. Exact emitted wrapper state/update except exposed pending signals, init removed for arbitrary-state step, macro read replaced by explicit physical-read oracle. Both collision schedules. Assumes memory relation; does not prove macro state relation, initial correspondence, four-state or Full equivalence.'),indent=2)+'\n')
with (D/'check.log').open('x') as log:
    try:code=subprocess.run([str(y),'-s','check.ys'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
    except subprocess.TimeoutExpired:code='TIMEOUT'
passed=code==0 and 'no model found: SUCCESS' in (D/'check.log').read_text()
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,exit_code=code,passed=passed,
    admitted_for_prediction=False,files={str(p):sha(p) for p in D.iterdir() if p.is_file()}),indent=2)+'\n')
print(code,passed)
