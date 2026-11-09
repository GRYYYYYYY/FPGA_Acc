import random
import subprocess
import tempfile
import unittest
from pathlib import Path

class ScoreTest(unittest.TestCase):
    def test_python_floor_and_weighted_score(self):
        rng=random.Random(30092026)
        cases=[([3,7,0,1],[2,8,1,0],[2,2,1]),
               ([2**64-1]*4,[0]*4,[2,2,1]),
               ([0]*4,[1]*4,[2,2,1])]
        for _ in range(2000):
            cases.append(([rng.randrange(1,2**60) for _ in range(4)],
                          [rng.randrange(2**60) for _ in range(4)],
                          [rng.randrange(8) for _ in range(3)]))
        expected=[]; payload=[str(len(cases))]
        for before,after,weights in cases:
            normalized=[((a-b)*2**20)//max(1,b) for b,a in zip(before,after)]
            expected.append(normalized[0]+sum(w*n for w,n in zip(weights,normalized[1:])))
            payload.append(' '.join(map(str,before+after+weights)))
        with tempfile.TemporaryDirectory() as directory:
            binary=Path(directory)/'score'
            subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',
                            str(Path(__file__).with_name('score_query.cpp')),'-o',str(binary)],check=True)
            result=subprocess.run([str(binary)],input='\n'.join(payload)+'\n',text=True,capture_output=True,check=True)
        self.assertEqual(list(map(int,result.stdout.split())),expected)

if __name__=='__main__': unittest.main()
