import sys,random,json,time
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent/'phase2_A/source'));sys.path.insert(0,str(D))
import reuse
from tileplace_v2 import TilePlaceV2Engine as E,V2Config
r=random.Random(20261110);e=E.__new__(E);e.pressure_prefix=True;e.profile=dict(index_build_s=0.,index_builds=0,cache_hits=0,cache_misses=0,cache_invalidations=0,path_queries=0);e._net_cost_cache={};memo=reuse.Memo();reuse.CAPACITY=16;count=0
for epoch in range(12):
 pressure={} if epoch==0 else {(x,y,x+1,y):r.randrange(1<<90) for x in range(-5,5) for y in range(-5,5)}
 e.pressure_q16=pressure;memo.reset()
 for _ in range(200):
  a=(r.randrange(-5,6),r.randrange(-5,6),0,0);b=r.choice([a,(r.randrange(-5,6),r.randrange(-5,6),0,0)]);e.positions={0:a,1:b}
  for i in range(2):
   actual=memo.get(e,0,1,e.positions,E._connection_congestion,True);expect=min(e._path_pressure_edgewalk(a[:2],b[:2],True),e._path_pressure_edgewalk(a[:2],b[:2],False));assert actual==expect;count+=1
# Dedicated stale-key negative control must disagree when both L routes gain pressure.
e.positions={0:(0,0,0,0),1:(2,2,0,0)};e.pressure_q16={};memo.reset();old=memo.get(e,0,1,e.positions,E._connection_congestion)
e.pressure_q16={(0,0,1,0):1<<80,(0,0,0,1):1<<80};fresh=E._connection_congestion(e,0,1,e.positions);assert memo.get(e,0,1,e.positions,E._connection_congestion)!=fresh
memo.reset();assert memo.get(e,0,1,e.positions,E._connection_congestion)==fresh
# Whole-score dependencies stay outside scalar memo: nonmoved extrema, criticality, routed timing, restore.
e.net_members={1:[0,1,2]};e.connections={1:[(0,1,5)]};e.block_nets={0:{1},1:{1},2:{1}};e.positions={0:(0,0,0,0),1:(2,2,0,0),2:(9,0,0,0)};e.path_edges_q16={(0,1):3};e.config=V2Config();e.guarded=[]
original=E._connection_congestion
for trial in [{0:(1,0,0,0)},{0:(2,2,0,0),1:(0,0,0,0)},{0:(1,0,0,0),1:(9,0,0,0),2:(0,0,0,0)}]:
 for pressure in [{},{(0,0,1,0):1<<80}]:
  e.pressure_q16=pressure;memo.reset()
  for far in [9,12]:
   e.positions[2]=(far,0,0,0)
   for crit in [5,20]:
    e.connections[1]=[(0,1,crit)];e.update_timing_feedback(({(0,1):crit},{0,1}));e._net_cost_cache.clear();candidate={**e.positions,**trial};ref=e._cost_pair({1},frozenset(trial),candidate)
    e._connection_congestion=lambda s,t,p:memo.get(e,s,t,p,original,True);e._net_cost_cache.clear();assert e._cost_pair({1},frozenset(trial),candidate)==ref;del e._connection_congestion;count+=1
    snap=e.snapshot();e.positions.update(trial);e.restore(snap);assert e.positions==snap
print(json.dumps({'status':'pass','comparisons':count,'stale_negative_control_detected':True,'cache_stats':dict(memo.stats),'covers':['empty/negative/zero/repeated coordinates','>64bit weights','capacity eviction and exact fallback','HPWL nonmoving extrema','criticality and routed feedback','swap and multi-member trials','restore','pressure replacement'],'limits':'synthetic cost vectors are not a full synthetic legal macro/chain controller fixture'}))
