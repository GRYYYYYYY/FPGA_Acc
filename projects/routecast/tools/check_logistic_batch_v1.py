"""Independent scalar BCE/gradient/update, finite differences and error atomicity."""
import math,random,json,ctypes as C
from pathlib import Path
from compiled_logistic_batch_v1 import matrix,gradient,train,library,BINARY
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def reference(rows,ys,w,lam):
 gradients=[0.0]*len(w);losses=[]
 for x,y in zip(rows,ys):
  z=w[0]+sum(a*b for a,b in zip(x,w[1:]));p=1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z));losses.append(max(z,0)-y*z+math.log1p(math.exp(-abs(z))));gradients[0]+=p-y
  for j,a in enumerate(x,1):gradients[j]+=(p-y)*a
 return sum(losses)/len(rows)+lam*sum(a*a for a in w[1:])/2,[a/len(rows)+(lam*w[j] if j else 0) for j,a in enumerate(gradients)]
def close(a,b,tol=1e-11):assert abs(a-b)<=tol*max(1,abs(a),abs(b)),(a,b)
def main():
 rng=random.Random(20261020);updates=0;finite_checks=0
 for trial in range(200):
  n,d=rng.randrange(1,10),rng.randrange(1,7);rows=[[rng.randrange(-9,10)/3 for _ in range(d)] for _ in range(n)];ys=[rng.randrange(2) for _ in range(n)];w=[rng.randrange(-5,6)/7 for _ in range(d+1)];lam=.001;data=matrix(rows,ys);a,g=gradient(data,w,lam);b,h=reference(rows,ys,w,lam);close(a,b)
  for x,y in zip(g,h):close(x,y)
  if trial<20:
   for j in range(d+1):
    hi=list(w);lo=list(w);hi[j]+=1e-5;lo[j]-=1e-5;numeric=(reference(rows,ys,hi,lam)[0]-reference(rows,ys,lo,lam)[0])/2e-5;close(numeric,g[j],1e-7);finite_checks+=1
  for iterations in [0,1,2,25]:
   step=1/(d+1);expected=[0.0]*(d+1)
   for _ in range(iterations):
    _,h=reference(rows,ys,expected,lam);expected=[x-step*y for x,y in zip(expected,h)];updates+=1
   out=train(data,iterations,lam,step)
   for x,y in zip(out['weights'],expected):close(x,y)
   loss,h=reference(rows,ys,expected,lam);close(out['final_loss'],loss);close(out['gradient_l2'],math.sqrt(sum(x*x for x in h)))
 for z in [-1000,1000]:
  loss,g=gradient(matrix([[1]],[int(z<0)]),[0,z]);assert math.isfinite(loss) and all(map(math.isfinite,g))
 rejected=0
 for call in [lambda:matrix([[float('nan')]],[0]),lambda:matrix([[1]],[.5]),lambda:matrix([[1],[2,3]],[0,1]),lambda:gradient(matrix([[1]],[0]),[0,float('inf')]),lambda:train(matrix([[1]],[0]),1,-1),lambda:train(matrix([[1]],[0]),1,step=0),lambda:train(matrix([[1]],[0]),True)]:
  try:call()
  except ValueError:rejected+=1
  else:raise AssertionError('invalid logistic input accepted')
 lib=library();x=(C.c_double*1)(float('nan'));y=(C.c_double*1)(0);w=(C.c_double*2)(73,79);stats=(C.c_double*3)(11,13,17);assert lib.rc_logistic_train(1,1,x,y,.001,2,.5,w,stats)!=0 and list(w)==[73,79] and list(stats)==[11,13,17];rejected+=1
 D=R/'experiments/logistic_batch_contract_v1_2026-10-20';D.mkdir(exist_ok=False);paths=[Path(__file__),R/'tools/compiled_logistic_batch_v1.py',R/'tools/soft_demand_cpp/logistic_batch_v1.cpp',BINARY,R/'build/logistic_batch_v1_2026-10-20/receipt.json'];(D/'verification.json').write_text(json.dumps({'status':'ALL200_SCALAR_GRADIENT_AND800_TRAINING_REFERENCES_PASS','random_models':200,'training_runs':800,'scalar_updates':updates,'finite_differences':finite_checks,'invalid_rejections':rejected,'bindings':{str(p):sha(p) for p in paths},'scope':'Deterministic logistic implementation, not convergence/quality claim. No real labels read.'},indent=2)+'\n');print('LOGISTIC_CONTRACT_PASS',updates,finite_checks,rejected)
if __name__=='__main__':main()
