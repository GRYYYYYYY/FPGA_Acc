import random,unittest
from dataclasses import replace
from rr_graph import RREdge
from budget_pin_candidates import BudgetPins
from test_pin_choice_catalog import CatalogTests
class BudgetPinTests(unittest.TestCase):
 def fixture(self):
  g=CatalogTests().fixture(True);nodes=dict(g.nodes);nodes[8]=replace(nodes[3],id=8)
  return replace(g,nodes=nodes,edges=g.edges+(RREdge(1,8,0,()),RREdge(8,3,0,()),RREdge(3,8,0,()),RREdge(7,8,0,())))
 def test_exhaustive_random_cost_delay_constraints(self):
  g=self.fixture();engine=BudgetPins(g);rng=random.Random(20261008)
  for _ in range(300):
   cost=[rng.randrange(8) for e in g.edges];delay=[rng.randrange(8) for e in g.edges];budget=rng.randrange(35);target=rng.randrange(2);blocked={e for e in range(len(g.edges)) if rng.randrange(6)==0};blocked_nodes={3} if rng.randrange(10)==0 else set();best=[]
   def visit(node,seen,path,c,d):
    if d>budget:return
    if node==6:best.append((c,d,path));return
    for eid in engine.outgoing[node]:
     dest=g.edges[eid].sink
     if eid in blocked or dest in blocked_nodes or dest in seen:continue
     if node==0 and dest not in {1,7}:continue
     if g.nodes[dest].type=='IPIN' and int(dict(g.nodes[dest].location)['ptc'])!=target:continue
     visit(dest,seen|{dest},path+[eid],c+cost[eid],d+delay[eid])
   visit(0,{0},[],0,0);r=engine.query(0,6,0,target,cost,delay,budget,blocked_nodes,blocked)
   if not best:self.assertEqual(r['status'],'UNREACHABLE')
   else:
    opt=min((c,d) for c,d,_ in best);self.assertEqual(r['status'],'FOUND');self.assertEqual((r['cost'],r['delay']),opt);self.assertIn((r['cost'],r['delay'],r['path']),best)
 def test_label_limit_is_not_infeasibility(self):
  e=BudgetPins(self.fixture());r=e.query(0,6,0,0,[0]*len(e.graph.edges),[0]*len(e.graph.edges),0,max_labels=1);self.assertEqual(r['status'],'LABEL_LIMIT');self.assertIsNone(r['path'])
 def test_invalid_constraints(self):
  e=BudgetPins(self.fixture());n=len(e.graph.edges)
  for extra in ({'budget':True},{'budget':-1},{'target_ptc':True},{'max_labels':0},{'blocked_nodes':{0}},{'blocked_edges':{True}},{'edge_delays':[True]*n}):
   args=dict(source=0,sink=6,source_ptc=0,target_ptc=0,edge_costs=[0]*n,edge_delays=[0]*n,budget=0);args.update(extra)
   with self.assertRaises(ValueError):e.query(**args)

 def test_pareto_tradeoff_not_min_delay_or_unconstrained_min_cost(self):
  g=self.fixture();nodes=dict(g.nodes);nodes[9]=replace(nodes[3],id=9);g=replace(g,nodes=nodes,edges=g.edges+(RREdge(3,9,0,()),RREdge(9,4,0,())))
  costs=[0]*len(g.edges);delays=[0]*len(g.edges);costs[2]=10;delays[2]=1;costs[9]=1;delays[9]=5;delays[4]=5;costs[13]=100;delays[14]=1;delays[8]=100
  engine=BudgetPins(g);tight=engine.query(0,6,0,0,costs,delays,7);loose=engine.query(0,6,0,0,costs,delays,10)
  self.assertEqual((tight['cost'],tight['delay']),(10,6));self.assertEqual((loose['cost'],loose['delay']),(1,10))
