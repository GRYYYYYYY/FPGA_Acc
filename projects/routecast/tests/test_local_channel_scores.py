import random,unittest,copy
from rr_graph import RRGraph,RRNode
from feedback_scores import scores
from local_channel_scores import LocalChannelScores
class LocalScoreTests(unittest.TestCase):
 def fixture(self):
  nodes={n:RRNode(n,'SOURCE' if n==0 else 'SINK' if n==7 else 'CHANX',1+(n%3),'NONE',(),(('xlow',str(n)),('xhigh',str(n+2)),('ylow','0'),('yhigh','0')),(),None) for n in range(8)}
  g=RRGraph(nodes,(),{}, {},{},'g');e={'connections':[{'net_id':0,'source':0,'sink':7}]};return g,e
 def test_500_random_replacements_match_independent_full_scores(self):
  g,e=self.fixture();model=LocalChannelScores(g);rng=random.Random(20261010)
  for _ in range(500):
   old={n for n in g.nodes if rng.randrange(2)};new={n for n in g.nodes if rng.randrange(2)};external={n:rng.randrange(5) for n in g.nodes};current={str(n):external[n]+int(n in old) for n in g.nodes};after={str(n):external[n]+int(n in new) for n in g.nodes};base=scores(g,e,current);snapshot=copy.deepcopy((base,old,new,external));self.assertEqual(model.replace_net(base,old,new,external),scores(g,e,after));self.assertEqual((base,old,new,external),snapshot)
 def test_shared_nodes_and_capacity_crossings(self):
  g,e=self.fixture();old={1,2};new={1,3};external={1:3,2:2,3:1};base=scores(g,e,{str(n):external.get(n,0)+int(n in old) for n in g.nodes});expected=scores(g,e,{str(n):external.get(n,0)+int(n in new) for n in g.nodes});self.assertEqual(LocalChannelScores(g).replace_net(base,[1,1,2],new,external),expected)
 def test_invalid_local_inputs(self):
  g,e=self.fixture();model=LocalChannelScores(g);base=scores(g,e,{})
  for old,new,external,score in ((set(),{99},{},base),({True},set(),{},base),(set(),{1},{1:True},base),(set(),{1},{1:-1},base),(set(),{1},{},{**base,'net_bbox_hpwl':True}),({1},set(),{},base)):
   with self.assertRaises(ValueError):model.replace_net(score,old,new,external)
