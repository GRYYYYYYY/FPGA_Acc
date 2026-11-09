"""Run additional fixed-parameter native adapter checks against archived runs."""
import argparse,concurrent.futures,json,subprocess,time,threading
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"cpp_snapshot"))
from audit_native_differential import audit

def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',nargs='+',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--runner',choices=['snapshot'],default='snapshot');a=p.parse_args()
 root=Path(__file__).resolve().parent.parent
 cohort=root/'experiments/tileplace_new_cohort_2026-09-29'
 a.output.mkdir(exist_ok=False)
 plans=[]
 for case in a.cases:
  original=cohort/case/'run_00/refinement_00.command.json'
  command=json.loads(original.read_text())[3:]
  command[1]=str(Path(__file__).with_name('run_cost_native.py'))
  index=command.index('--implementation-manifest');del command[index:index+2]
  directory=a.output/case;directory.mkdir()
  for flag,name in [('--work','work'),('--output-place','final.place'),('--report','report.json'),('--timing-report','timing.json')]:command[command.index(flag)+1]=str((directory/name).resolve())
  command+=['--cpp-binary',str(a.binary.resolve())]
  (directory/'command.json').write_text(json.dumps(command,indent=2)+'\n')
  plans.append((case,directory,command,cohort/case/'run_00/report.json'))
 (a.output/'plan.json').write_text(json.dumps({'cases':a.cases,'scope':'implementation equivalence using existing parameters, not a new QoR study'},indent=2)+'\n')
 completed=[]; lock=threading.Lock()
 def record(row):
  with lock:
   completed.append(row)
   temporary=a.output/'progress.tmp'
   temporary.write_text(json.dumps({'expected_cases':a.cases,'completed_cases':completed},indent=2)+'\n')
   temporary.replace(a.output/'progress.json')
  return row
 def run(plan):
  case,directory,command,reference=plan;start=time.monotonic();print('START '+case,flush=True)
  with (directory/'stdout.log').open('w') as out,(directory/'stderr.log').open('w') as err:result=subprocess.run(command,stdout=out,stderr=err)
  (directory/'process.json').write_text(json.dumps({'returncode':result.returncode,'wall_s':time.monotonic()-start})+'\n')
  if result.returncode:return record({'case':case,'status':'fail','returncode':result.returncode})
  try:receipt=audit(directory,reference)
  except Exception as error:return record({'case':case,'status':'audit_fail','error':str(error)})
  (directory/'differential_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
  print('DONE '+case,flush=True)
  return record({'case':case,**receipt})
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,plans))
 summary={'status':'pass' if all(r['status']=='pass' for r in rows) else 'fail','cases':rows}
 (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='cases'}))
 return 0 if summary['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
