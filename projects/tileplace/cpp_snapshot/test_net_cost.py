import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'tools'))
from tileplace_v2 import TilePlaceV2Engine

class NetCostTest(unittest.TestCase):
    def test_reference_cost_pairs(self):
        rng=random.Random(29092026)
        payload=['500']; expected=[]
        for _ in range(500):
            engine=TilePlaceV2Engine.__new__(TilePlaceV2Engine)
            engine.positions={i:(rng.randrange(-10,11),rng.randrange(-10,11),0,0) for i in range(20)}
            changed=frozenset(rng.sample(range(20),rng.randrange(21)))
            after={i:((rng.randrange(-10,11),rng.randrange(-10,11),0,0) if i in changed else p)
                   for i,p in engine.positions.items()}
            pressure={(x,y,x+1,y):rng.randrange(1<<25) for x in range(-10,11) for y in [-3,0,3]}
            pressure.update({(x,y,x,y+1):rng.randrange(1<<25) for y in range(-10,11) for x in [-3,0,3]})
            engine.pressure_q16=pressure
            engine._net_cost_cache={}
            engine.net_members={i:rng.sample(range(20),rng.randrange(1,10)) for i in range(5)}
            engine.connections={i:[(m[0],sink,rng.randrange(1<<20)) for sink in m[1:]]
                                for i,m in engine.net_members.items()}
            engine.path_edges_q16={(rng.randrange(20),rng.randrange(20)):rng.randrange(1<<30) for _ in range(15)}
            a,b=engine._cost_pair(range(5),changed,after); expected.append((*a,*b))
            payload.append(f'20 {len(pressure)} 5 {len(engine.path_edges_q16)}')
            for i,p in engine.positions.items(): payload.append(' '.join(map(str,(*p[:2],*after[i][:2],int(i in changed)))))
            payload += [' '.join(map(str,(*edge,w))) for edge,w in pressure.items()]
            for i,members in engine.net_members.items():
                connections=engine.connections[i]; payload.append(f'{len(members)} {len(connections)}')
                payload.append(' '.join(map(str,members)))
                payload += [' '.join(map(str,c)) for c in connections]
            payload += [' '.join(map(str,(*edge,w))) for edge,w in engine.path_edges_q16.items()]
        with tempfile.TemporaryDirectory() as directory:
            binary=Path(directory)/'net_query'
            subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'net_query.cpp'),'-o',str(binary)],check=True)
            result=subprocess.run([str(binary)],input='\n'.join(payload)+'\n',text=True,capture_output=True,check=True)
        self.assertEqual([tuple(map(int,line.split())) for line in result.stdout.splitlines()],expected)

if __name__=='__main__': unittest.main()
