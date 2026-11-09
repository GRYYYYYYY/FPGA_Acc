"""Frozen one-round multicritical preparation, per-stage cost/failure receipts."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_top3r2_preparation_v2_2026-10-06';out.mkdir();names=['diagnose_ex5p_top3r2_timing_arcs','trace_ex5p_top3r2_packed_pins','bind_ex5p_top3r2_rr_paths','prepare_ex5p_top3r2_cohort','bind_ex5p_top3r2_output_timing_arcs','prepare_ex5p_top3r2_complete_cohort','diagnose_ex5p_top3r2_empty_delay','verify_ex5p_top3r2_empty_delay','trial_ex5p_top3r2_selector'];parent=root/'experiments/ex5p_top3_joint_repair_2026-10-06/receipt.json';p={'parent_sha256':sha(parent),'stages':names,'sources_sha256':{n:sha(root/'tools'/(n+'.py')) for n in names+['select_multicritical_targets']},'feedback_rounds':1,'top_k':3,'max_targets':3,'released_connections_max':200,'max_labels':10000,'budget_ns':1,'per_stage_timeout_s':180,'scope':'One new development feedback preparation round on latestcandidate, same deterministic selection rule. No outcome-based budget extension; nativequality/fullflow evaluation still required.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[];start=time.monotonic()
for i,n in enumerate(names):
 log=out/(str(i)+'.log');begin=time.monotonic()
 with log.open('w') as stream:code=subprocess.run([sys.executable,str(root/'tools'/(n+'.py'))],cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 rows.append({'tool':n,'exit_code':code,'wall_s':time.monotonic()-begin,'log_sha256':sha(log)});print(n,code,rows[-1]['wall_s'],flush=True)
 if code:break
r={'stages':rows,'complete':len(rows)==len(names) and all(x['exit_code']==0 for x in rows),'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
