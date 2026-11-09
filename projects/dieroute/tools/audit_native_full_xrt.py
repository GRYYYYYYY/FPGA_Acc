#!/usr/bin/env python3
"""Run the complete native cohort, protocol, baseline and XRT dispatch audits."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
from compare_native_first_repeat import compare
from audit_native_xrt_dispatch import bind_dispatch


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()


def main():
 if not __debug__:raise RuntimeError('audits require assertions')
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ['run','baseline','output']:parser.add_argument('--'+name,type=Path,required=True)
 args=parser.parse_args();run=args.run.resolve();baseline=args.baseline.resolve();out=args.output.resolve()
 manifest=json.loads((run/'manifest.json').read_text());reference=json.loads((baseline/'manifest.json').read_text())
 assert manifest['status']=='passed' and manifest['inputs_unchanged']
 assert reference['status']=='passed' and reference['inputs_unchanged']
 command=manifest['command'];expected=reference['command']
 assert len(command)==len(expected)==25 and command[23:]==['2','1']
 assert command[1:7]==expected[1:7] and command[8:11]==expected[8:11] and command[12:]==expected[12:]
 assert int(command[11])>=1
 out.mkdir(parents=True,exist_ok=False);sources=out/'sources';sources.mkdir()
 tools=Path(__file__).resolve().parent
 names=['audit_native_full_xrt.py','compare_native_first_repeat.py','audit_native_xrt_dispatch.py','audit_native_cohort.py','audit_native_owner.py','audit_native_parallel.py','audit_native_label_transport.py','audit_native_persistent_shadows.py','audit_native_summary_hbm.py','audit_native_owner_publish.py','audit_native_net_commit.py','audit_net_commit.py','run_native_case.py']
 bindings={}
 for name in names:
  path=tools/name;bindings[str(path)]=sha(path);shutil.copy2(path,sources/name)
 for path in [run/'manifest.json',baseline/'manifest.json',run/'run.log']:
  bindings[str(path)]=sha(path)
 for root,record in [(run,manifest),(baseline,reference)]:
  for name,digest in record['artifacts'].items():
   path=root/name;assert sha(path)==digest,path;bindings[str(path)]=digest
  for name,digest in record['inputs'].items():
   assert sha(name)==digest,name;bindings[name]=digest
 receipt={'status':'running','started_ns':time.time_ns(),'inputs':bindings,'run':str(run),'baseline':str(baseline),'board_result':False,'research_complete':False}
 def save():
  tmp=out/'audit.tmp';tmp.write_text(json.dumps(receipt,indent=2)+'\n');tmp.replace(out/'audit.json')
 save()
 try:
  stages=[('cohort',['--run',str(run),'--output',str(out/'cohort')]),('parallel',['--run',str(run),'--cohort-audit',str(out/'cohort'),'--output',str(out/'parallel')])]
  for stage,arguments in stages:
   script=sources/('audit_native_'+stage+'.py')
   with (out/(stage+'.log')).open('w') as log:
    status=subprocess.run([sys.executable,str(script),*arguments],stdout=log,stderr=subprocess.STDOUT).returncode
   assert status==0,(stage,status)
   receipt[stage]='passed';save()
  proof=json.loads((out/'parallel/audit.json').read_text())
  receipt['dispatch']=bind_dispatch(run,proof)
  receipt['baseline_first_repeat']=compare(run,baseline)
  assert all(sha(path)==digest for path,digest in bindings.items()),'inputs changed during audit'
  receipt.update(status='passed',inputs_unchanged=True,finished_ns=time.time_ns(),scope='Complete selected native cohort and recorded protocol replay, deterministic first-repeat comparison and actual XRT dispatch; physical performance, full-design QoR and hardware search remain unproven')
 except BaseException as error:
  receipt.update(status='failed',error=repr(error),finished_ns=time.time_ns());save();raise
 save();print(json.dumps({'status':receipt['status'],'dispatch':receipt['dispatch']}))

if __name__=='__main__':main()
