"""Small synthetic legal-site macro/swap/chain fixture; no native-quality claim."""
import sys,json,collections
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent/'phase2_A/source'));sys.path.insert(0,str(D))
from tileplace_v2 import TilePlaceV2Engine as E,V2Config
from reuse import Memo

def fixture(cache):
 e=E.__new__(E);e.config=V2Config(critical_distance_guard_q=0);e.pressure_prefix=True;e.profile=dict(index_build_s=0.,index_builds=0,cache_hits=0,cache_misses=0,cache_invalidations=0,path_queries=0);e._net_cost_cache={};e.pressure_q16={};e.memo=Memo();e.memo.reset()
 e.positions={0:(0,0,0,0),1:(0,1,0,0),2:(3,0,0,0),3:(3,1,0,0),4:(4,0,0,0),5:(5,0,0,0),6:(6,0,0,0),7:(7,0,0,0)};e.initial_positions=dict(e.positions)
 e.units=[(0,1),(2,3),(4,),(5,),(6,),(7,)];e.unit_by_block={b:u for u in e.units for b in u};e.fixed_units=set();e.block_by_id={b:{'block_id':b,'logical_type':'clb'} for b in e.positions};e.site_by_loc={(x,y,0,0):{'physical_type':'clb'} for x in range(8) for y in range(3)};e.sites_by_page_type=collections.defaultdict(list)
 for loc in e.site_by_loc:e.sites_by_page_type[e.page_key(loc),'clb'].append(loc)
 for v in e.sites_by_page_type.values():v.sort(key=lambda l:(l[3],l[1],l[0],l[2]))
 e.net_members={0:list(e.positions)};e.block_nets={b:{0} for b in e.positions};e.connections={0:[(0,4,10),(1,5,20),(2,6,30),(3,7,40)]};e.guarded=[];e.path_edges_q16={(0,4):7};e.focus_blocks=set();trace=[];kinds=collections.Counter()
 if cache:e._connection_congestion=lambda s,t,p:e.memo.get(e,s,t,p,E._connection_congestion)
 original=e._make_transaction
 def make(kind,units,trial):
  kinds[kind]+=1;beforeafter=e._cost_pair({0},frozenset(trial),{**e.positions,**trial});v=original(kind,units,trial);trace.append([kind,units,sorted(trial.items()),beforeafter,None if v is None else v.audit()]);return v
 e._make_transaction=make
 outcomes=[]
 for epoch,pressure in enumerate([{}, {(0,0,1,0):1<<80,(0,0,0,1):1<<80},{}]):
  e.pressure_q16=pressure;e.memo.reset();e.update_timing_feedback(({(0,4):7+epoch},{0,1,2,3,4,5,6,7}));e.connections[0][0]=(0,4,10+epoch)
  for color in range(4):
   batch,audit=e.propose_color(color);outcomes.append([audit,[t.audit() for t in batch]]);snap=e.snapshot();e.apply(batch);e.restore(snap)
   again,aa=e.propose_color(color,{t.transaction_id for t in batch});outcomes.append([aa,[t.audit() for t in again]])
 # Reject illegal duplicate sites and guard-triggered move, without a fabricated score.
 occ={v:k for k,v in e.positions.items()};assert not e._valid_trial({4:(5,0,0,0),5:(5,0,0,0)},frozenset({4,5}),occ)
 e.guarded=[(0,4,60000,0)];assert e._make_transaction('move',((4,),),{4:(7,2,0,0)}) is None
 return trace,outcomes,dict(kinds)
a=fixture(False);b=fixture(True);assert a==b;assert all(a[2].get(k,0)>0 for k in ['move','swap','macro_swap','chain2','chain3']);print(json.dumps({'status':'pass','transaction_attempts':len(a[0]),'kind_counts':a[2],'batch_comparisons':len(a[1]),'covers':['macro whole-member translation and macro_swap','swap','chain2','chain3','no-good filtering and tie/conflict selection','apply/restore','pressure replacement and previous snapshot restoration','routed/criticality update','guard rejection','duplicate-site legality rejection'],'scope':'synthetic legal-site enumerator, not VPR legality or full design coverage'},indent=2))
