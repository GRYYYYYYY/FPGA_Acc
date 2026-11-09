"""Positive random coverage supplement, independent Fraction reference unchanged."""
import json,random,struct,hashlib
from pathlib import Path
from check_map_materialize_v2 import ref
from compiled_map_materialize_v2 import materialize,BINARY
R=Path(__file__).resolve().parents[1];D=R/'experiments/map_materialize_positive_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);rng=random.Random(51120261020);nodes=0
 for _ in range(1000):
  n=64;term=[rng.randrange(2) for _ in range(n)];allowed=[rng.randrange(2) for _ in range(n)];pairs=[]
  for t in term:
   a=rng.randrange(133)<<23|rng.randrange(1<<23);b=a if t else rng.randrange(133)<<23|rng.randrange(1<<23);pairs.append((a,b))
  data=b''.join(struct.pack('<II',*p) for p in pairs);bits=struct.pack('>I',rng.randrange(0x3f800001)).hex();scale=rng.randrange(1,2**64);q=rng.randrange(1,2**32);assert materialize(data,allowed,term,bits,scale,q)==ref(data,allowed,term,bits,scale,q);nodes+=n
 rejected=0
 for bits,data,term in [('7fc00000',struct.pack('<ff',1,1),[0]),('bf800000',struct.pack('<ff',1,1),[0]),('00000000',struct.pack('<ff',1,2),[1]),('00000000',struct.pack('<II',0x7fc00000,0),[0]),('00000000',struct.pack('<ff',-1,0),[0])]:
  try:materialize(data,[1],term,bits,1,1)
  except ValueError:rejected+=1
  else:raise AssertionError('invalid materializer accepted')
 files=[Path(__file__),R/'tools/check_map_materialize_v2.py',R/'tools/compiled_map_materialize_v2.py',BINARY];(D/'verification.json').write_text(json.dumps({'status':'ALL1000_RANDOM_VALID_VECTORS64000_NODES_AND5_EXPLICIT_REJECTIONS_PASS','valid_vectors':1000,'nodes':nodes,'explicit_rejections':rejected,'bindings':{str(p):sha(p) for p in files},'scope':'Supplement to500 random overflow rejections and real NET0 vector equality; standalone only.'},indent=2)+'\n');print('POSITIVE_MATERIALIZER_PASS',nodes,rejected)
if __name__=='__main__':main()
