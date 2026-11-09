"""Subdivide exactly the timeout target slices, preserving original miter premises."""
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_remaining_register_step_sat_v1_2026-10-09';plan=json.load(open(P/'partition_plan.json'));coverage=json.load(open(P/'partition_coverage_audit.json'));base=(P/'miter.v').read_text();ys=(P/'check.ys').read_text();Y='/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';chunks=[]
for c in plan['chunks']:
 r=json.load(open(P/f'partition_{c["index"]}_receipt.json'))
 if r['exit_code']!='TIMEOUT':continue
 for lo in range(c['low'],c['high']+1,16):
  hi=min(lo+15,c['high']);chunks.append({'name':f'sub_{c["index"]}_{lo}','low':lo,'high':hi,'source_q':c['source_q'][lo-c['low']:hi-c['low']+1]})
assert {q for c in chunks for q in c['source_q']}==set(coverage['remaining_source_q'])
(P/'subpartition_plan.json').write_text(json.dumps({'chunks':chunks,'target_bits':128,'preserves_all_parent_premises':True},indent=2)+'\n')
for c in chunks:
 name=c['name'];receipt=P/(name+'_receipt.json')
 if receipt.exists():continue
 v=P/(name+'.v');script=P/(name+'.ys');log=P/(name+'.log');v.write_text(base.replace('assign bad=|(source_next ^ mapped_next);',f'assign bad=|(source_next[{c["high"]}:{c["low"]}] ^ mapped_next[{c["high"]}:{c["low"]}]);'));script.write_text(ys.replace('read_verilog miter.v',f'read_verilog {v.name}').replace('model.json',name+'_model.json'))
 with log.open('w') as out:
  try:code=subprocess.run([Y,'-s',script.name],cwd=P,stdout=out,stderr=subprocess.STDOUT,timeout=15).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 text=log.read_text();result={'exit_code':code,'sat_success':code==0 and 'no model found: SUCCESS' in text,'counterexample':code==0 and 'model found: FAIL' in text,'source_q':c['source_q'],'scope':'Original conditional one-step next-state miter, shared-state aliases and killReg0 retained; no Full admission.','functional_admission':False,'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),P/'cuts.json',P/'subpartition_plan.json',v,script,log]}};receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'name':name,'exit':code,'success':result['sat_success'],'counterexample':result['counterexample']}),flush=True)
