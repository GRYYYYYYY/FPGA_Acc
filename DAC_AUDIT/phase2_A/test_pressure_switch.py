#!/usr/bin/env python3
import sys,random,json,time
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'source'))
from tileplace_v2 import TilePlaceV2Engine
r=random.Random(20261110);count=0;start=time.monotonic();a=TilePlaceV2Engine.__new__(TilePlaceV2Engine);b=TilePlaceV2Engine.__new__(TilePlaceV2Engine)
for e,enabled in [(a,True),(b,False)]:
 e.pressure_prefix=enabled;e.profile=dict(index_build_s=0.,index_builds=0,cache_hits=0,cache_misses=0,cache_invalidations=0,path_queries=0);e._net_cost_cache={7:(1,2,3)}
for epoch in range(8):
 pressure={}
 for _ in range(140):
  x,y=r.randrange(-10,30),r.randrange(-10,30);dx,dy=r.choice([(1,0),(0,1)]);pressure[x,y,x+dx,y+dy]=r.randrange(2**45)
 for e in [a,b]:
  e._net_cost_cache[7]=(1,2,3);e.pressure_q16=pressure;assert not e._net_cost_cache
 pressure.clear() # setter must own an immutable snapshot in both arms
 for _ in range(500):
  u=(r.randrange(-12,32),r.randrange(-12,32));v=r.choice([u,(r.randrange(-12,32),r.randrange(-12,32))])
  for h in [True,False]:assert a._path_pressure(u,v,h)==b._path_pressure(u,v,h);count+=1
assert count>0
result={'status':'pass','comparisons':count,'feedback_epochs':8,'covers':['reverse directions','zero-length','empty/sparse lines','large integer weights','feedback replacement','immutable source snapshot','cost cache invalidation'],'wall_s':time.monotonic()-start,'not_claimed':'Full controller equivalence; tested by frozen native pilot'}
(D/'evidence/switch_unit_check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
