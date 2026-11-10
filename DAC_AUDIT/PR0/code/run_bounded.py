"""Run only frozen PR0 CPU work. Sequential own process groups, bounded AS/time.
All diagnostic subprocess attempts remain in the ledger; no adaptive retry.
"""
import pathlib,subprocess,os,sys,time,json,resource,signal,hashlib
root=pathlib.Path(__file__).resolve().parents[3]
out=pathlib.Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
code=root/'DAC_AUDIT/PR0/code';pr=root/'projects/persistroute'
protocol=json.loads((root/'DAC_AUDIT/PR0/PR0_PROTOCOL.json').read_text())
ledger=[];used=0
allowed=sorted(os.sched_getaffinity(0))
# Observe CPU counters twice to choose four relatively idle allowed cores.
def counters():
 d={}
 for line in pathlib.Path('/proc/stat').read_text().splitlines():
  a=line.split()
  if a and a[0].startswith('cpu') and a[0][3:].isdigit():
   vals=list(map(int,a[1:]));d[int(a[0][3:])]=(sum(vals[:8]),vals[3]+vals[4])
 return d
c1=counters();time.sleep(.2);c2=counters()
cores=sorted(allowed,key=lambda c:1-(c2[c][1]-c1[c][1])/max(1,c2[c][0]-c1[c][0]))[:4]
def limits():
 os.setsid();resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2);os.sched_setaffinity(0,cores);os.nice(10)
def run(name,argv,timeout):
 global used
 if used>=3600:raise RuntimeError('cumulative budget exhausted')
 start=time.perf_counter();wall=time.time();status='completed';duration=min(timeout,3600-used)
 with (out/(name+'.stdout')).open('w') as stdout,(out/(name+'.stderr')).open('w') as stderr:
  p=subprocess.Popen(['/usr/bin/time','-f','%e,%M','-o',str(out/(name+'.time'))]+list(map(str,argv)),stdout=stdout,stderr=stderr,preexec_fn=limits,cwd=root)
  try:rc=p.wait(timeout=duration)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGKILL);rc=p.wait();status='timeout'
 elapsed=time.perf_counter()-start;used+=elapsed
 ledger.append(dict(name=name,argv=list(map(str,argv)),start_unix=wall,wall_s=elapsed,exit_code=rc,status=status,cpu_affinity=cores,peak_rss_kib_time_file=name+'.time',budget_used_s=used))
 (out/'run_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
 if rc:raise RuntimeError(name+' failed; no automatic retry')
run('generate',[sys.executable,code/'generate_reference.py',pr/'src/search_hbm.cpp',out/'wide_search.cpp'],30)
run('compile',['g++','-std=c++17','-O2','-pthread','-I'+str(code),'-I'+str(pr/'include'),code/'pr0.cpp',out/'wide_search.cpp']+[pr/'src'/s for s in ['search_hbm.cpp','commit_hbm.cpp','multiqueue.cpp','hbm_cmodel_backend.cpp','accelerated_pathfinder.cpp','pathfinder.cpp']]+['-o',out/'pr0'],180)
(out/'executable_identity.json').write_text(json.dumps({'sha256':hashlib.sha256((out/'pr0').read_bytes()).hexdigest(),'path':str(out/'pr0'),'generated_source_sha256':hashlib.sha256((out/'wide_search.cpp').read_bytes()).hexdigest(),'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0]},indent=2)+'\n')
run('synthetic',[out/'pr0','synthetic',out/'counterexamples'],120)
for case in protocol['cases']:
 name=case['name'];prefix=case['input_prefix'];caseout=out/name
 run(name+'_capture',[out/'pr0','capture',prefix,caseout],600)
# Correctness for both cases must finish before performance starts.
for case in protocol['cases']:
 name=case['name'];run(name+'_performance',[out/'pr0','performance',case['input_prefix'],out/name],600)
