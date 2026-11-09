"""Independent dense Gaussian Newton step and Hessian finite differences."""
import json,random,math,ctypes as C
from pathlib import Path
from compiled_logistic_batch_v1 import matrix,gradient
from compiled_logistic_newton_v1 import hessian,train,library,BINARY
from check_logistic_batch_v1 import reference,close
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def H_reference(rows,w,lam):
 q=len(w);H=[[0.0]*q for _ in range(q)]
 for row in rows:
  v=[1]+row;z=sum(a*b for a,b in zip(w,v));p=1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z));c=p*(1-p)
  for i in range(q):
   for j in range(q):H[i][j]+=c*v[i]*v[j]/len(rows)
 for i in range(1,q):H[i][i]+=lam
 return H
def gaussian(A,b):
 a=[list(row)+[v] for row,v in zip(A,b)];n=len(b)
 for i in range(n):
  k=max(range(i,n),key=lambda k:abs(a[k][i]));a[i],a[k]=a[k],a[i];pivot=a[i][i];assert pivot!=0;a[i]=[v/pivot for v in a[i]]
  for k in range(n):
   if k==i:continue
   scale=a[k][i];a[k]=[u-scale*v for u,v in zip(a[k],a[i])]
 return [row[-1] for row in a]
def main():
 rng=random.Random(20261020);finite=0;stationary=0;failures=0
 for trial in range(150):
  n,d=rng.randrange(2,13),rng.randrange(1,7);rows=[[rng.randrange(-6,7)/3 for _ in range(d)] for _ in range(n)];ys=[rng.randrange(2) for _ in rows];ys[0]=0;ys[-1]=1;data=matrix(rows,ys);w=[rng.randrange(-6,7)/5 for _ in range(d+1)];actual=hessian(data,w);ref=H_reference(rows,w,.001)
  for a,b in zip(actual,ref):
   for x,y in zip(a,b):close(x,y)
  if trial<15:
   for j in range(d+1):
    hi=list(w);lo=list(w);hi[j]+=1e-5;lo[j]-=1e-5;_,gh=gradient(data,hi);_,gl=gradient(data,lo)
    for i in range(d+1):close((gh[i]-gl[i])/2e-5,actual[i][j],1e-7);finite+=1
  zero=[0.0]*(d+1);loss,g=reference(rows,ys,zero,.001);direction=gaussian(H_reference(rows,zero,.001),g);dot=sum(a*b for a,b in zip(g,direction));alpha=1
  for _ in range(40):
   candidate=[-alpha*v for v in direction]
   if reference(rows,ys,candidate,.001)[0]<=loss-1e-4*alpha*dot:break
   alpha/=2
  one=train(data,max_iterations=1)
  for a,b in zip(one['weights'],candidate):close(a,b,1e-9)
  out=train(data);loss,g=reference(rows,ys,out['weights'],.001);close(loss,out['final_loss']);close(max(map(abs,g)),out['gradient_inf']);assert all(a['loss']>=b['loss']-1e-12 for a,b in zip(out['trace'],out['trace'][1:]));assert (out['status']=='NUMERIC_STATIONARITY')==(out['gradient_inf']<=1e-10);stationary+=out['status']=='NUMERIC_STATIONARITY';failures+=out['status']!='NUMERIC_STATIONARITY'
 intercept=train(matrix([[0],[0],[0]],[0,0,1]));assert intercept['status']=='NUMERIC_STATIONARITY';close(intercept['weights'][0],math.log(.5),1e-9);close(intercept['weights'][1],0)
 limit=train(matrix([[-1],[1]],[0,1]),max_iterations=0);assert limit['status']=='ITERATION_LIMIT' and limit['weights']==[0,0]
 invalid=0
 for call in [lambda:train(matrix([[0],[1]],[0,0])),lambda:train(matrix([[0],[1]],[0,1]),regularization=0),lambda:train(matrix([[0],[1]],[0,1]),tolerance=0),lambda:train(matrix([[0],[1]],[0,1]),max_backtracks=0)]:
  try:call()
  except ValueError:invalid+=1
  else:raise AssertionError('invalid Newton problem accepted')
 lib=library();x=(C.c_double*2)(0,1);y=(C.c_double*2)(0,0);w=(C.c_double*2)(71,73);stats=(C.c_double*6)(*([79]*6));trace=(C.c_double*404)(*([83]*404));assert lib.rc_logistic_newton(2,1,x,y,.001,100,40,1e-10,w,stats,trace)<0 and list(w)==[71,73] and list(stats)==[79]*6 and list(trace)==[83]*404;invalid+=1
 D=R/'experiments/logistic_newton_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/compiled_logistic_newton_v1.py',R/'tools/soft_demand_cpp/logistic_newton_v1.cpp',R/'tools/soft_demand_cpp/logistic_batch_v1.cpp',R/'tools/check_logistic_batch_v1.py',BINARY,R/'build/logistic_newton_v1_2026-10-20/receipt.json'];(D/'verification.json').write_text(json.dumps({'status':'ALL150_HESSIANS_GAUSSIAN_NEWTON_STEPS_AND_STATIONARITY_AUDITS_PASS','random_models':150,'finite_difference_entries':finite,'stationary_random_runs':stationary,'preserved_nonstationary_random_runs':failures,'invalid_atomic_rejections':invalid,'bindings':{str(p):sha(p) for p in files},'scope':'Numerical solver correctness only; nonstationary termination retained and not success. No real labels or optimum certificate.'},indent=2)+'\n');print('NEWTON_CONTRACT_PASS',finite,stationary,failures,invalid)
if __name__=='__main__':main()
