"""Owned stdlib ctypes matrices for qualified deterministic logistic regression."""
import ctypes as C,math
from array import array
from pathlib import Path
R=Path(__file__).resolve().parents[1];BINARY=R/'build/logistic_batch_v1_2026-10-20/logistic.so'
def matrix(rows,labels):
 rows=list(rows);labels=list(labels)
 if not rows or not rows[0] or len(rows)!=len(labels) or any(len(r)!=len(rows[0]) for r in rows):raise ValueError('matrix dimensions')
 x=array('d',(v for row in rows for v in row));y=array('d',labels)
 if any(not math.isfinite(v) for v in x) or any(v not in [0,1] for v in y):raise ValueError('matrix values')
 return len(rows),len(rows[0]),x,y
def library():
 lib=C.CDLL(str(BINARY));pointer=C.POINTER(C.c_double);base=[C.c_uint64,C.c_uint64,pointer,pointer,C.c_double];lib.rc_logistic_gradient.argtypes=base+[pointer,pointer,pointer];lib.rc_logistic_gradient.restype=C.c_int;lib.rc_logistic_train.argtypes=base+[C.c_uint64,C.c_double,pointer,pointer];lib.rc_logistic_train.restype=C.c_int;return lib
def buffers(data):
 n,d,x,y=data
 if type(n) is not int or type(d) is not int or n<1 or not 1<=d<=4096 or len(x)!=n*d or len(y)!=n or x.typecode!='d' or y.typecode!='d':raise ValueError('owned matrix layout')
 return (C.c_double*len(x)).from_buffer(x),(C.c_double*len(y)).from_buffer(y)
def gradient(data,weights,regularization=.001):
 n,d,x,y=data
 if len(weights)!=d+1:raise ValueError('weight dimensions')
 a,b=buffers(data);w=(C.c_double*(d+1))(*weights);g=(C.c_double*(d+1))();loss=C.c_double();rc=library().rc_logistic_gradient(n,d,a,b,regularization,w,C.byref(loss),g)
 if rc:raise ValueError('logistic gradient rejected '+str(rc))
 return loss.value,list(g)
def train(data,iterations=1000,regularization=.001,step=None):
 n,d,x,y=data
 if type(iterations) is not int or iterations<0:raise ValueError('iteration domain')
 a,b=buffers(data);w=(C.c_double*(d+1))();stats=(C.c_double*3)();step=1/(d+1) if step is None else step;rc=library().rc_logistic_train(n,d,a,b,regularization,iterations,step,w,stats)
 if rc:raise ValueError('logistic trainer rejected '+str(rc))
 return {'weights':list(w),'initial_loss':stats[0],'final_loss':stats[1],'gradient_l2':stats[2],'iterations':iterations,'step':step,'regularization':regularization}
