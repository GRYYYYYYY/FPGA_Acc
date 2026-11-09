from dataclasses import replace
import unittest
import test_hybrid_repair as fixture
from rr_graph import RREdge
from regional_search_cache import CachedRegionalSearch
from lazy_region_search import LazyRegionalSearch
from hybrid_repair import repair

class CacheTests(unittest.TestCase):
    def test_hit_has_same_paths_without_search_and_no_mutable_alias(self):
        g,_,_=fixture.RepairTests().setup_case();cache=CachedRegionalSearch(g)
        first,_=cache.search(0,{5});path=first.paths[5];first.paths.clear()
        second,details=cache.search(0,{5})
        self.assertEqual(second.paths[5],path);self.assertEqual(second.edge_visits,0)
        self.assertTrue(details['cache_hit']);second.paths.clear()
        self.assertEqual(cache.search(0,{5})[0].paths[5],path)
    def test_other_sink_changes_region_and_requires_miss(self):
        g,_,_=fixture.RepairTests().setup_case();nodes=dict(g.nodes)
        loc=dict(nodes[2].location);loc.update(xlow='10',xhigh='10')
        nodes[2]=replace(nodes[2],location=tuple(sorted(loc.items())))
        loc=dict(nodes[5].location);loc.update(xlow='10',xhigh='10')
        nodes[6]=replace(nodes[5],id=6,location=tuple(sorted(loc.items())))
        g=replace(g,nodes=nodes,edges=g.edges+(RREdge(2,6,0,()),))
        cache=CachedRegionalSearch(g)
        narrow,_=cache.search(0,{5});broad,d=cache.search(0,{5,6})
        self.assertNotIn(5,narrow.paths);self.assertIn(5,broad.paths)
        self.assertFalse(d['cache_hit']);self.assertEqual(cache.misses,2)
        expected,_=LazyRegionalSearch(g).search(0,{5,6})
        self.assertEqual(broad.paths,expected.paths)
    def test_cached_repair_matches_fresh_net_union(self):
        g,e,c=fixture.RepairTests().setup_case();cache=CachedRegionalSearch(g)
        factory=lambda graph,margin:cache
        cold=repair(g,e,c,search_type=factory)
        warm=repair(g,e,c,search_type=factory)
        fresh=repair(g,e,c,search_type=LazyRegionalSearch)
        for key in ('connections','node_occupancy','methods','completed'):
            self.assertEqual(warm[key],fresh[key]);self.assertEqual(cold[key],fresh[key])
        self.assertEqual(warm['repair_work']['regional_edge_visits'],0)
        self.assertEqual(cache.hits,1)

    def test_eviction_is_bounded(self):
        g,_,_=fixture.RepairTests().setup_case();cache=CachedRegionalSearch(g,max_groups=1)
        cache.search(0,{5});cache.search(0,set());cache.search(0,{5})
        self.assertEqual(cache.misses,3);self.assertEqual(len(cache.cache),1)

if __name__=='__main__':unittest.main()
