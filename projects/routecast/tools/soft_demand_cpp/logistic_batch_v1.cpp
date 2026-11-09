#include <cmath>
#include <cstdint>
#include <vector>
#include <limits>
#include <algorithm>
using U=uint64_t;
static double sigmoid(double z){if(z>=0){double t=std::exp(-z);return 1/(1+t);}double t=std::exp(z);return t/(1+t);}
static int valid(U n,U d,const double*x,const double*y,double lambda){
 if(!n||!d||d>4096||n>std::numeric_limits<U>::max()/d||!x||!y||!std::isfinite(lambda)||lambda<0)return -1;
 for(U i=0;i<n*d;i++)if(!std::isfinite(x[i]))return -2;
 for(U i=0;i<n;i++)if(y[i]!=0.0&&y[i]!=1.0)return -2;
 return 0;
}
static int compute(U n,U d,const double*x,const double*y,double lambda,const std::vector<double>&w,std::vector<double>&g,double*loss){
 std::fill(g.begin(),g.end(),0);double value=0;
 for(U i=0;i<n;i++){
  const double*row=x+i*d;double z=w[0];for(U j=0;j<d;j++)z+=w[j+1]*row[j];if(!std::isfinite(z))return -3;
  double residual=sigmoid(z)-y[i];g[0]+=residual;for(U j=0;j<d;j++)g[j+1]+=residual*row[j];
  if(loss)value+=std::max(z,0.0)-y[i]*z+std::log1p(std::exp(-std::abs(z)));
 }
 for(U j=0;j<=d;j++){g[j]/=n;if(j)g[j]+=lambda*w[j];if(!std::isfinite(g[j]))return -3;}
 if(loss){value/=n;for(U j=1;j<=d;j++)value+=lambda*w[j]*w[j]/2;if(!std::isfinite(value))return -3;*loss=value;}
 return 0;
}
extern "C" int rc_logistic_gradient(U n,U d,const double*x,const double*y,double lambda,const double*weights,double*loss,double*gradient){
 try{int rc=valid(n,d,x,y,lambda);if(rc)return rc;if(!weights||!loss||!gradient)return -1;std::vector<double>w(weights,weights+d+1),g(d+1);for(double a:w)if(!std::isfinite(a))return -2;double v;rc=compute(n,d,x,y,lambda,w,g,&v);if(rc)return rc;*loss=v;std::copy(g.begin(),g.end(),gradient);return 0;}catch(...){return -9;}
}
extern "C" int rc_logistic_train(U n,U d,const double*x,const double*y,double lambda,U iterations,double step,double*weights,double*statistics){
 try{int rc=valid(n,d,x,y,lambda);if(rc)return rc;if(!weights||!statistics||!std::isfinite(step)||step<=0)return -1;std::vector<double>w(d+1,0),g(d+1);double first,last;rc=compute(n,d,x,y,lambda,w,g,&first);if(rc)return rc;
 for(U iteration=0;iteration<iterations;iteration++){
  if(iteration){rc=compute(n,d,x,y,lambda,w,g,nullptr);if(rc)return rc;}
  for(U j=0;j<=d;j++){w[j]-=step*g[j];if(!std::isfinite(w[j]))return -3;}
 }
 rc=compute(n,d,x,y,lambda,w,g,&last);if(rc)return rc;double norm=0;for(double a:g)norm+=a*a;if(!std::isfinite(norm))return -3;statistics[0]=first;statistics[1]=last;statistics[2]=std::sqrt(norm);std::copy(w.begin(),w.end(),weights);return 0;
 }catch(...){return -9;}
}
