"""Observe original audit/comparison processes, then bind their complete evidence."""
import json,time,subprocess,shutil
from pathlib import Path
from conv_layer_csr_completion_chain import identity,sha
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'

def main():
 expected=[('matched_length_switch_control_full_xml_audit','tools/audit_stereo_length_switch_control_full_xml.py'),('matched_model_comparison_completion_chain','tools/stereo_matched_comparison_completion_chain.py')]
 observed={}
 for name,script in expected:
  root=BASE/name
  if (root/'receipt.json').exists():observed[name]=None;continue
  matches=[]
  for p in Path('/proc').iterdir():
   if p.name.isdigit():
    item=identity(int(p.name))
    if item and script in item['argv']:matches.append(item)
  assert len(matches)==1;observed[name]=matches[0]
 out=BASE/'full_cost_binding_completion_chain';out.mkdir();(out/'source').mkdir()
 names=['stereo_full_cost_binding_completion_chain.py','conv_layer_csr_completion_chain.py','bind_stereo_matched_comparison_full_cost_audit.py','compare_stereo_matched_evaluations.py']
 sources={name:sha(ROOT/'tools'/name) for name in names}
 for name in names:shutil.copyfile(ROOT/'tools'/name,out/'source'/name)
 protocol={'observed_original_processes':observed,'parent_protocol_sha256':{name:sha(BASE/name/'protocol.json') for name,script in expected},'sources':sources,'scope':'wait for original audit and comparison without restart; bind full cost transport to matched metrics; no feedback benefit'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps({'stage':'waiting_original_evidence','processes':observed}),flush=True)
 while True:
  missing=[name for name,script in expected if not (BASE/name/'receipt.json').exists()]
  if not missing:break
  for name in missing:
   process=observed[name]
   if process is None or identity(process['pid'])!=process:raise RuntimeError('original process missing without receipt: '+name)
  time.sleep(10)
 assert all(sha(BASE/name/'protocol.json')==digest for name,digest in protocol['parent_protocol_sha256'].items())
 assert all(sha(ROOT/'tools'/name)==digest for name,digest in sources.items())
 command=['python3','-u','tools/bind_stereo_matched_comparison_full_cost_audit.py'];start=time.monotonic();result=subprocess.run(command,cwd=ROOT)
 stage={'command':command,'exit_code':result.returncode,'wall_s':time.monotonic()-start};(out/'stage.json').write_text(json.dumps(stage,indent=2)+'\n')
 if result.returncode:raise RuntimeError('full evidence binding failed; no restart')
 assert all(sha(ROOT/'tools'/name)==digest for name,digest in sources.items())
 receipt={'protocol_sha256':sha(out/'protocol.json'),'stage':stage,'binding_receipt_sha256':sha(BASE/'matched_comparison_full_cost_evidence/receipt.json'),'parent_receipt_sha256':{name:sha(BASE/name/'receipt.json') for name,script in expected},'scope':protocol['scope']}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
