"""Resume only partitions without terminal receipts; keep full target coverage."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_remaining_register_step_sat_v1_2026-10-09';plan=json.load(open(P/'partition_plan.json'));base=(P/'miter.v').read_text();ys=(P/'check.ys').read_text();Y='/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
for c in plan['chunks']:
 i=c['index'];receipt=P/f'partition_{i}_receipt.json'
 if receipt.exists():continue
 lo,hi=c['low'],c['high'];v=P/f'partition_{i}.v';script=P/f'partition_{i}.ys';log=P/f'partition_{i}.log'
 v.write_text(base.replace('assign bad=|(source_next ^ mapped_next);',f'assign bad=|(source_next[{hi}:{lo}] ^ mapped_next[{hi}:{lo}]);'))
 script.write_text(ys.replace('read_verilog miter.v',f'read_verilog partition_{i}.v').replace('model.json',f'partition_{i}_model.json'))
 with log.open('w') as out:
  try:code=subprocess.run([Y,'-s',script.name],cwd=P,stdout=out,stderr=subprocess.STDOUT,timeout=30).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 text=log.read_text();r={'exit_code':code,'sat_success':code==0 and 'no model found: SUCCESS' in text,'counterexample':code==0 and 'model found: FAIL' in text,'source_q':c['source_q'],'scope':'Same conditional binary next-state miter and shared-state/killReg0 premises as parent; no Full admission.','functional_admission':False,'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),P/'cuts.json',P/'miter.v',P/'partition_plan.json',v,script,log]}}
 receipt.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'partition':i,'exit':code,'success':r['sat_success'],'counterexample':r['counterexample']}),flush=True)
