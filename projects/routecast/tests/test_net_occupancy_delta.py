import unittest,random
from collections import Counter
from net_occupancy_delta import replace_net

class DeltaTests(unittest.TestCase):
    def test_sequential_updates_match_independent_full_rebuild(self):
        rng=random.Random(20261006);capacities=[rng.randrange(4) for _ in range(40)]
        nets={k:set(rng.sample(range(40),rng.randrange(12))) for k in range(12)}
        occ=Counter(n for nodes in nets.values() for n in nodes)
        over=lambda values:sum(max(0,v-capacities[n]) for n,v in values.items())
        total=over(occ)
        for step in range(500):
            net=rng.randrange(12);new=set(rng.sample(range(40),rng.randrange(12)));before=occ.copy()
            staged,count,dirty=replace_net(occ,nets[net],new,capacities,total)
            self.assertEqual(occ,before);self.assertEqual(dirty,nets[net]^new)
            nets[net]=new;full=Counter(n for nodes in nets.values() for n in nodes)
            self.assertEqual(staged,full);self.assertEqual(count,over(full))
            occ,total=staged,count
    def test_invalid_does_not_mutate_and_zero_cleanup(self):
        old=Counter({1:1});self.assertEqual(replace_net(old,{1},set(),[1,1],0),(Counter(),0,{1}))
        with self.assertRaises(ValueError):replace_net(old,{0},set(),[1,1],0)
        self.assertEqual(old,Counter({1:1}))
if __name__=='__main__':unittest.main()
