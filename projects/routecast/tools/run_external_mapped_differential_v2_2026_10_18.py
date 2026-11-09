"""Finite upstream bus-vector differential test of source RTL and mapped BLIF."""
import sys,json,subprocess,os,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 src=R/'experiments/prospective_external_family_source_v2_2026-10-18';blif=R/'experiments/prospective_external_family_compile_cut_v2_2026-10-18/design.blif';runtime=R/'experiments/prospective_external_family_sim_runtime_v1_2026-10-18/root/usr';iv=runtime/'bin/iverilog';vvp=runtime/'bin/vvp';lib=runtime/'lib/x86_64-linux-gnu/ivl';yosys=Path(json.loads((src/'source_verification.json').read_text())['yosys_path']);out=R/'experiments/prospective_external_family_mapped_differential_v2_2026-10-18';out.mkdir(exist_ok=False);rtl=sorted((src/'upstream/src/rtl').glob('*.v'));tb=src/'upstream/src/tb/tb_chacha.v';bindings={str(p):sha(p) for p in [Path(__file__),blif,yosys,iv,vvp,*rtl,tb]};env=os.environ.copy();ld=R/'experiments/prospective_external_family_runtime_v1_2026-10-18/tcl-root/usr/lib/x86_64-linux-gnu';env['LD_LIBRARY_PATH']=str(ld)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');commands=f'read_blif "{blif}"; rename chacha mapped_chacha; techmap; opt; write_verilog -noattr "{out}/mapped.v"'
 with (out/'conversion.log').open('x') as log:code=subprocess.call([str(yosys),'-Q','-T','-p',commands],env=env,cwd=out,stdout=log,stderr=subprocess.STDOUT)
 assert code==0
 ports=[f'.{p}(tb.{w})' for p,w in [('clk','tb_clk'),('reset_n','tb_reset_n'),('cs','tb_cs'),('we','tb_write_read')]]
 for name,width,signal in [('addr',8,'tb.tb_address'),('write_data',32,'tb.tb_data_in'),('read_data',32,'gate_data')]:
  ports.extend('.\\'+name+'['+str(i)+'] ('+signal+'['+str(i)+'])' for i in range(width))
 harness='module differential;\n tb_chacha tb(); wire [31:0] gate_data; integer checks=0; reg reset_seen=0;\n mapped_chacha gate('+','.join(ports)+');\n always @(posedge tb.tb_clk) if (!tb.tb_reset_n) reset_seen<=1;\n always @(negedge tb.tb_clk) begin #1; if(reset_seen) begin checks=checks+1; if ((gate_data !== tb.tb_data_out) || (^gate_data === 1\'bx) || (^tb.tb_data_out === 1\'bx)) $fatal(1,"DIFFERENTIAL_FAIL cycle=%0d source=%h gate=%h",checks,tb.tb_data_out,gate_data); end end\n final $display("DIFFERENTIAL_CHECKS %0d", checks);\n endmodule\n'
 (out/'harness.sv').write_text(harness);cmd=[str(iv),'-B',str(lib),'-g2012','-s','differential','-o',str(out/'sim.vvp'),*[str(p) for p in rtl],str(tb),str(out/'mapped.v'),str(out/'harness.sv')]
 with (out/'compile.log').open('x') as log:code=subprocess.call(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT)
 assert code==0
 with (out/'simulation.log').open('x') as log:
  child=subprocess.Popen([str(vvp),'-M',str(lib),str(out/'sim.vvp')],cwd=out,stdout=log,stderr=subprocess.STDOUT);(out/'live_process.json').write_text(json.dumps(dict(pid=child.pid)));print('DIFFERENTIAL CHILD',child.pid,flush=True);code=child.wait()
 text=(out/'simulation.log').read_text();matches=re.findall(r'DIFFERENTIAL_CHECKS (\d+)',text);checks=int(matches[-1]) if matches else 0;passed=code==0 and checks>0 and 'All 03 test cases completed successfully' in text and 'DIFFERENTIAL_FAIL' not in text
 for path,h in bindings.items():assert sha(path)==h
 files={str(p):sha(p) for p in out.iterdir() if p.is_file()}
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='source_mapped_finite_bus_differential_pass' if passed else 'differential_not_passed',bindings=bindings,files=files,exit_code=code,post_reset_samples=checks,passed=passed,scope='Same original upstream bus stimulus drives original RTL and mapped BLIF lowered through pinned Yosys techmap/opt before Verilog emission. This diagnostic changes simulation representation; original indexed-LUT X failure remains preserved. Negedge+1 sampled32bit outputs must both be defined and case-equal after observed reset edge. Finite vectors only; not packed/placed/timing, all-cycle/four-state formal or heldout qualification.'),f,indent=2)
 print('DIFFERENTIAL TERMINAL',code,passed,checks,flush=True)
if __name__=='__main__':main()
