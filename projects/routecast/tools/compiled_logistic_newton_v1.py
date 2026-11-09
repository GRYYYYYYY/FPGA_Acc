"""Owned deterministic Newton/Hessian adapter, diagnostic nonconvergence retained."""
import ctypes as C
from pathlib import Path
from compiled_logistic_batch_v1 import buffers,matrix
R=Path(__file__).resolve().parents[1];BINARY=R/'build/logistic_newton_v1_2026-10-20/newton.so'
def library():
 lib=C.CDLL(str(BINARY));p=C.POINTER(C.c_double);base=[C.c_uint64,C.c_uint64,p,p,C.c_double];lib.rc_logistic_hessian.argtypes=base+[p,p];lib.rc_logistic_hessian.restype=C.c_int;lib.rc_logistic_newton.argtypes=base+[C.c_uint64,C.c_uint64,C.c_double,p,p,p];lib.rc_logistic_newton.restype=C.c_int;return lib
def hessian(data,weights,regularization=.001):
 n,d,x,y=data;a,b=buffers(data)
 if len(weights)!=d+1:raise ValueError('Hessian weight dimensions')
 w=(C.c_double*(d+1))(*weights);out=(C.c_double*((d+1)**2))();rc=library().rc_logistic_hessian(n,d,a,b,regularization,w,out)
 if rc:raise ValueError('Newton Hessian rejected '+str(rc))
 return [list(out[i*(d+1):(i+1)*(d+1)]) for i in range(d+1)]
def train(data,max_iterations=100,regularization=.001,max_backtracks=40,tolerance=1e-10):
 n,d,x,y=data
 if type(max_iterations) is not int or not 0<=max_iterations<=10000 or type(max_backtracks) is not int or not 1<=max_backtracks<=1000:raise ValueError('Newton iteration domain')
 a,b=buffers(data);w=(C.c_double*(d+1))();stats=(C.c_double*6)();trace=(C.c_double*(4*(max_iterations+1)))();rc=library().rc_logistic_newton(n,d,a,b,regularization,max_iterations,max_backtracks,tolerance,w,stats,trace)
 if rc<0:raise ValueError('Newton trainer rejected '+str(rc))
 steps=int(stats[5]);return {'weights':list(w),'initial_loss':stats[0],'final_loss':stats[1],'gradient_l2':stats[2],'gradient_inf':stats[3],'iterations':int(stats[4]),'termination_code':rc,'status':{0:'NUMERIC_STATIONARITY',1:'ITERATION_LIMIT',2:'BACKTRACK_FAILURE',3:'CHOLESKY_FAILURE'}[rc],'max_iterations':max_iterations,'max_backtracks':max_backtracks,'tolerance':tolerance,'regularization':regularization,'trace':[{'iteration':int(trace[4*i]),'loss':trace[4*i+1],'gradient_inf':trace[4*i+2],'accepted_step':trace[4*i+3]} for i in range(steps)]}
