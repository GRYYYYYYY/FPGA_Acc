"""Exercise fanout/present interactions using the actual host and independent replay."""
import argparse,hashlib,json,os,shlex,subprocess,sys
from pathlib import Path
from rr_fanout_present_replay import replay

p=argparse.ArgumentParser(description=__doc__)
for n in ['variant','fixture','output']:p.add_argument(n,type=Path)
a=p.parse_args();root,fixture,out=[x.resolve() for x in [a.variant,a.fixture,a.output]];out.mkdir(exist_ok=False)
binary=root/'build/dieroute_rr'
env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
env.update(DIEROUTE_COST_BITS='64',DIEROUTE_VPR_STYLE_COST='1',DIEROUTE_TREE_TIMING_WEIGHT_Q='128',DIEROUTE_MIN_TIMING_ITERATIONS='6',DIEROUTE_MAX_ITERATIONS='6',PERSISTROUTE_TIMING_COMMAND=shlex.join([sys.executable,str(fixture/'timing.py')]))
records=[]
for mode in [0,1,2]:
 for order in [0,1]:
  previous=None
  for i in range(5):
   name=f'present{mode}_fanout{order}_{i}';prefix=out/name
   e=dict(env,DIEROUTE_PRESENT_SCHEDULE_MODE=str(mode),DIEROUTE_NET_DISPATCH_ORDER=str(order),DIEROUTE_ORDINARY_SCHEDULE_MODE='0')
   with (out/(name+'.log')).open('w') as log:subprocess.run([str(binary),str(fixture/'input'),str(fixture/'topology'),str(prefix),'flat'],env=e,stdout=log,stderr=subprocess.STDOUT,check=True)
   proof=replay(fixture/'input',prefix,0,4,6,net_order_mode=order,present_mode=mode)
   assert proof['cpu_legal'] and proof['final_resources_and_costs_byte_equivalent']
   report=json.loads(Path(str(prefix)+'.json').read_text());assert report['present_schedule_mode']==mode and report['net_dispatch_order']==order;report.pop('wall_ms')
   hashes={f.name[len(name):]:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.glob(name+'.*') if f.suffix not in ['.log','.json']}
   if previous is not None:assert previous==(report,hashes)
   previous=(report,hashes)
   records.append(dict(name=name,present_mode=mode,fanout=order,replay=proof))
# An observed present2/fanout1 route must reject either wrong policy.
pristine=out/'present2_fanout1_0';rejected=[]
for label,kwargs in [('present',dict(present_mode=0,net_order_mode=1)),('fanout',dict(present_mode=2,net_order_mode=0))]:
 try:replay(fixture/'input',pristine,0,4,6,**kwargs)
 except AssertionError:rejected.append(label)
 else:raise AssertionError('wrong policy accepted '+label)
for schedule in [1,2]:
 e=dict(env,DIEROUTE_PRESENT_SCHEDULE_MODE='2',DIEROUTE_ORDINARY_SCHEDULE_MODE=str(schedule),DIEROUTE_NET_DISPATCH_ORDER='1')
 with (out/f'forbidden_schedule{schedule}.log').open('w') as log:
  rc=subprocess.run([str(binary),str(fixture/'input'),str(fixture/'topology'),str(out/f'forbidden{schedule}'),'flat'],env=e,stdout=log,stderr=subprocess.STDOUT).returncode
 assert rc!=0
 text=(out/f'forbidden_schedule{schedule}.log').read_text();assert 'present schedule requires standalone serial bulk wide negotiation' in text
files=[binary,Path(__file__).resolve(),Path(__file__).with_name('rr_fanout_present_replay.py'),*fixture.glob('input.*'),*fixture.glob('topology.*'),fixture/'timing.py']
with (out/'audit.json').open('x') as f:json.dump(dict(status='thirty_actual_fanout_present_host_runs_independently_replayed',runs=records,wrong_policy_rejections=rejected,forbidden_schedule_rejections=[1,2],source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},scope='Sixarms x5 actual host runs,6STAepochs,fanouts3/2/2/1. Full independent dispatch/seed/resource/version/cost replay and repeat determinism. Wrongpolicy and forbiddenmode rejection. Small CPU fixture only,not native QoR or physical evidence.',board_result=False,research_complete=False),f,indent=2)
print('PASS actual host runs',len(records),'wrong policies',rejected)
