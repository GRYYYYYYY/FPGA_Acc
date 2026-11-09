"""Deterministic CART raw-feature adapter with exact-rational split comparisons."""
import ctypes as C,math
from pathlib import Path
from compiled_logistic_batch_v1 import matrix,buffers
R=Path(__file__).resolve().parents[1];BINARY=R/'build/fixed_cart_v1_2026-10-20/cart.so'
def library():
 lib=C.CDLL(str(BINARY));p=C.POINTER(C.c_double);lib.rc_fixed_cart.argtypes=[C.c_uint64,C.c_uint64,p,p,C.c_uint64,C.c_uint64,C.c_uint64,C.POINTER(C.c_int64),p,C.POINTER(C.c_uint64)];lib.rc_fixed_cart.restype=C.c_int;return lib
def train(data,depth=8,minleaf=64):
 n,d,x,y=data
 if type(depth) is not int or not 0<=depth<=16 or type(minleaf) is not int or not 1<=minleaf<=1000000:raise ValueError('tree shape domain')
 a,b=buffers(data);capacity=2**(depth+1)-1;metadata=(C.c_int64*(capacity*5))();thresholds=(C.c_double*capacity)();count=C.c_uint64();rc=library().rc_fixed_cart(n,d,a,b,depth,minleaf,capacity,metadata,thresholds,C.byref(count))
 if rc:raise ValueError('CART trainer rejected '+str(rc))
 nodes=[{'feature':metadata[5*i],'left':metadata[5*i+1],'right':metadata[5*i+2],'rows':metadata[5*i+3],'positive':metadata[5*i+4],'threshold':thresholds[i]} for i in range(count.value)]
 return {'nodes':nodes,'depth_limit':depth,'minimum_child_rows':minleaf,'columns_count':d,'training_rows':n,'leaf_policy':'(positive+1)/(rows+2)'}
def leaf(row,model):
 if len(row)!=model['columns_count'] or any(not math.isfinite(x) for x in row):raise ValueError('CART query domain')
 nodes=model['nodes'];at=0
 for _ in range(len(nodes)):
  node=nodes[at]
  if node['feature']==-1:return node
  at=node['left'] if row[node['feature']]<=node['threshold'] else node['right']
 raise ValueError('cyclic tree')
def probability(row,model):
 node=leaf(row,model);return (node['positive']+1)/(node['rows']+2)
