import unittest
from buffered_delay_cost import BufferedDelayCost
from selected_path_budgets import budgets
from test_tree_rc import fixture

class BudgetTests(unittest.TestCase):
    def test_sparse_selected_graph_keeps_raw_edge_identity(self):
        from types import SimpleNamespace
        from streaming_prediction_audit import Edges
        g=fixture('buffer');edge=g.edges[1]
        sparse=SimpleNamespace(nodes={n:g.nodes[n] for n in (edge.source,edge.sink)},
                               edges=Edges({1:edge},len(g.edges)),switches=g.switches)
        row={'connection_id':7,'source':edge.source,'sink':edge.sink,'physical_edge_ids':[1]}
        self.assertEqual(budgets(sparse,[row])[7],BufferedDelayCost(g).path_delay(edge.source,[1]))
    def test_exact_reference(self):
        g=fixture('buffer');model=BufferedDelayCost(g)
        rows=[{'connection_id':i,'source':0,'sink':g.edges[e].sink,'physical_edge_ids':[e]} for i,e in enumerate((0,1))]
        self.assertEqual(budgets(g,rows),{r['connection_id']:model.path_delay(0,r['physical_edge_ids']) for r in rows})
    def test_reject_invalid(self):
        g=fixture('buffer');row={'connection_id':0,'source':0,'sink':1,'physical_edge_ids':[0]}
        for changes in ({'physical_edge_ids':None},{'physical_edge_ids':[True]},{'source':True},{'sink':999},{'physical_edge_ids':[1]}):
            with self.assertRaises(ValueError):budgets(g,[{**row,**changes}])
        with self.assertRaises(ValueError):budgets(g,[row,row])
        for graph in (fixture(),fixture('buffer',1)):
            with self.assertRaises(ValueError):budgets(graph,[row])
