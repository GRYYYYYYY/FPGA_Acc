"""Symbolic per-address invariant and matched arbitrary initialization obligations."""
import hashlib
import json
import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'ram_word_relation_v1_2026-10-09'; D.mkdir(exist_ok=False)
proof=E/'emitted_ram_relational_step_v1_2026-10-09/receipt.json'
receipt=json.loads(proof.read_text()); assert receipt['passed']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in receipt['bindings'].items():assert sha(Path(p))==h
y=Path(next(p for p in receipt['bindings'] if p.endswith('/bin/yosys')))
rtl='''module step(input [9:0] tracked,pa,wa,input pw,we,
input [19:0] physical_word,pd,data,output bad);
// Pre-state relation at an arbitrary tracked address.
wire [19:0] logical_word=(pw && pa==tracked) ? pd : physical_word;
// Physical macro applies the previous pending write; logical model applies current write.
wire [19:0] next_physical=(pw && pa==tracked) ? pd : physical_word;
wire [19:0] next_logical=(we && wa==tracked) ? data : logical_word;
// Next pending state is exactly current input write.
wire [19:0] related_next=(we && wa==tracked) ? data : next_physical;
assign bad=next_logical!=related_next;
endmodule
module initial_relation(input [19:0] arbitrary_word,arbitrary_output,
input [9:0] tracked,pa,input [19:0] pd,raw,fwd,input hit,output bad);
// Actual wrapper controls pw=0, er=0; data and visible output remain arbitrary matched.
wire pw=1'b0,er=1'b0;
wire [19:0] logical_word=arbitrary_word;
wire [19:0] physical_word=arbitrary_word;
wire [19:0] held=arbitrary_output;
wire [19:0] actual=er ? (hit ? fwd : raw) : held;
wire [19:0] related=(pw && pa==tracked) ? pd : physical_word;
assign bad=(logical_word!=related) || (actual!=arbitrary_output);
endmodule
'''
(D/'relation.v').write_text(rtl)
# Mutation changes only the physical state update, leaving the logical specification intact.
mutation=rtl.replace('wire [19:0] next_physical=(pw && pa==tracked) ? pd : physical_word;',
    'wire [19:0] next_physical=physical_word;')
(D/'mutation.v').write_text(mutation)
cases=[('step','relation.v','step',True),('initial','relation.v','initial_relation',True),('mutation','mutation.v','step',False)]
for name,src,top,_ in cases:
    (D/(name+'.ys')).write_text(f'read_verilog {src}\nhierarchy -check -top {top}\nproc\nflatten\nopt\ncheck -assert\nsat -prove bad 0 -show-inputs\n')
bindings={str(p):sha(p) for p in [Path(__file__),proof,y,*D.iterdir()] if p.is_file()}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,timeout_s_per_case=60,
    scope='Symbolic 10-bit tracked address and 20-bit word: memory relation preservation plus arbitrary matched initialization, under explicit single-write macro update. No array expansion or restricted addresses. Algebraic contract obligations, not proof of native macro implementation, cross-read consistency, four-state or Full equivalence.'),indent=2)+'\n')
results=[]
for name,src,top,expect_pass in cases:
    with (D/(name+'.log')).open('x') as log:
        try:code=subprocess.run([str(y),'-s',name+'.ys'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
        except subprocess.TimeoutExpired:code='TIMEOUT'
    log=(D/(name+'.log')).read_text()
    passed=code==0 and 'no model found: SUCCESS' in log
    counterexample=code==0 and 'model found: FAIL' in log
    valid=passed if expect_pass else counterexample
    results.append(dict(name=name,exit_code=code,passed=passed,counterexample=counterexample,expected_result_observed=valid))
out=dict(results=results,passed=all(r['expected_result_observed'] for r in results),bindings=bindings,
    admitted_for_prediction=False,files={str(p):sha(p) for p in D.iterdir() if p.is_file()})
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(results))
assert out['passed']
