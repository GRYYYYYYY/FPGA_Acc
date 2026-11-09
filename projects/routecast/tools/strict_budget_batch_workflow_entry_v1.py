"""Complete cohort preflight before any command, current inputs checked at each launch."""
import json,subprocess,time
from pathlib import Path
from certified_budget_batch_gate_v1 import preflight_batch
from certified_budget_execution_gate_v2 import InvalidEvidence
from pre_route_endpoints import sha

def execute_batch(authority,cases,output):
 if any(not c.get('command') for c in cases):raise ValueError('Every case needs a command')
 output=Path(output);output.mkdir(exist_ok=False);start=time.perf_counter()
 result=preflight_batch(authority,cases)
 protocol=dict(preflight=result,plans=[dict(command=list(c['command']),cwd=str(Path(c['cwd']).resolve())) for c in cases],source_sha256=sha(Path(__file__)))
 pp=output/'protocol.json';pp.write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for index,(case,decision) in enumerate(zip(cases,result['decisions'])):
  code=None;launched=False
  if decision['run_candidate_pipeline']:
   # Recheck the whole authenticated closure at launch: earlier commands can change evidence.
   if any(sha(p)!=h for p,h in result['bindings'].items()):raise InvalidEvidence('Evidence changed before candidate launch')
   launched=True
   with (output/f'candidate_{index}.log').open('x') as log:
    code=subprocess.run(case['command'],cwd=case['cwd'],stdout=log,stderr=subprocess.STDOUT).returncode
  rows.append(dict(index=index,decision=decision['decision'],candidate_launched=launched,candidate_exit_code=code,candidate_quality_accepted=False))
 report=dict(protocol_sha256=sha(pp),rows=rows,entry_seconds=time.perf_counter()-start,full_original_input_workflow_seconds=None,scope='Batch provided-floor admission and actual command entry. Revalidates full proof closure before every allowed launch; all skips launch nothing. Exit status is not quality acceptance. Prior floor generation excluded; no route speedup claim.')
 (output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');return report
