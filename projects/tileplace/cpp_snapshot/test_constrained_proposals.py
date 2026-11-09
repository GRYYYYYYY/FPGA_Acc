"""Differential candidates with macros, layers, subtiles and constraint unions."""
import random,subprocess,tempfile,unittest
from collections import defaultdict
from pathlib import Path
from compare_proposals import TilePlaceV2Engine,V2Config,payload,parse
from native_adapter import color_payload
ROOT=Path(__file__).resolve().parent

def engine(seed):
 rng=random.Random(seed);e=TilePlaceV2Engine.__new__(TilePlaceV2Engine)
 e.config=V2Config(page_width=3,page_height=2,candidate_limit=128,chain_candidate_limit=16,
                   routed_timing_weight=2,critical_distance_guard_q=0)
 e.positions={0:(0,0,0,0),1:(1,0,1,1),2:(4,0,0,0),3:(5,0,1,1),
              4:(7,1,0,0),5:(-1,-1,0,0),6:(2,1,0,0)}
 e.block_by_id={id:{'logical_type':'clb','initial':dict(zip(['x','y','subtile','layer'],p))}
                for id,p in e.positions.items()}
 e.block_by_id[5]['logical_type']='dsp'
 e.units=[(0,1),(2,3),(4,),(5,),(6,)]
 e.unit_by_block={id:u for u in e.units for id in u}
 if seed%4==1:
  e.block_by_id[2]['fixed']=True
  e.block_by_id[2]['fixed_location']={'x':4,'y':None,'subtile':None,'layer':0}
 if seed%4==2:e.block_by_id[4]['fixed']=True
 if seed%4==3:
  e.block_by_id[0]['region']=[0,-1,3,2,0]
  e.block_by_id[1]['region']=[{'xmin':0,'ymin':-1,'xmax':4,'ymax':2,'layer_low':0,'layer_high':1,'subtile':1},
                             {'xmin':5,'ymin':0,'xmax':8,'ymax':1,'layer_low':1,'layer_high':1,'subtile':-1}]
 if seed%3==1:e.block_by_id[6]['region']=[0,0,4,2]
 if seed%3==2:e.block_by_id[4]['region']=[{'xmin':6,'ymin':0,'xmax':8,'ymax':2,'layer_low':0,'layer_high':0,'subtile':0}]
 e.fixed_units={u for u in e.units if any(e.block_by_id[id].get('fixed') for id in u)}
 e.site_by_loc={ (x,y,s,l):{'physical_type':'clb'} for x in range(-2,9) for y in range(-1,3) for s in range(2) for l in range(2)}
 e.site_by_loc[e.positions[5]]={'physical_type':'dsp'}
 e.sites_by_page_type=defaultdict(list)
 for p,site in e.site_by_loc.items():e.sites_by_page_type[(e.page_key(p),site['physical_type'])].append(p)
 e.net_members={0:[0,1,4],2:[2,3,6],5:[0,2,4,6]}
 e.connections={0:[(0,4,50000),(1,4,30000)],2:[(2,6,40000),(3,6,20000)],5:[(0,6,35000),(2,4,45000)]}
 e.block_nets=defaultdict(set)
 for net,members in e.net_members.items():
  for id in members:e.block_nets[id].add(net)
 e.path_edges_q16={(0,4):100000,(2,6):70000};e.focus_blocks={0,2,4,6}
 e.pressure_q16={(x,0,x+1,0):rng.randrange(200000) for x in range(-2,8)}
 e.guarded=[];e._net_cost_cache={}
 return e

class ConstrainedProposalTest(unittest.TestCase):
 def test_complete_candidates(self):
  kinds=set();checked=0
  with tempfile.TemporaryDirectory() as directory:
   binary=Path(directory)/'query'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'proposal_query.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    e=engine(seed);occupied={p:id for id,p in e.positions.items()}
    for index,u in enumerate(e.units):
     reference=e._transactions_for_unit(u,occupied)
     expected=sorted((t.transaction_id,t.score_q20) for t in reference)
     result=subprocess.run([str(binary)],input=payload(e,index),text=True,capture_output=True,check=True)
     self.assertEqual(parse(result.stdout),expected,msg=f'seed {seed}, unit {u}')
     kinds.update(t.kind for t in reference);checked+=1
    for color in range(4):
     first,_=e.propose_color(color)
     forbidden={first[0].transaction_id} if first else set()
     reference,_=e.propose_color(color,forbidden)
     result=subprocess.run([str(binary),'--color'],input=color_payload(e,color,forbidden),
                           text=True,capture_output=True,check=True)
     self.assertEqual(parse(result.stdout),sorted((t.transaction_id,t.score_q20) for t in reference),
                      msg=f'constrained color seed {seed}, color {color}')
  self.assertIn('macro_swap',kinds)
  self.assertIn('move',kinds)
  self.assertEqual(checked,60)

if __name__=='__main__':unittest.main()
