#include "logistic_batch_v1.cpp"
static long double objective(U n,U d,const double*x,const double*y,double lambda,const std::vector<double>&w){
 long double total=0;
 for(U i=0;i<n;i++){long double z=w[0];for(U j=0;j<d;j++)z+=(long double)w[j+1]*x[i*d+j];total+=std::max(z,(long double)0)-y[i]*z+std::log1p(std::exp(-std::abs(z)));}
 total/=n;for(U j=1;j<=d;j++)total+=(long double)lambda*w[j]*w[j]/2;return total;
}
static int hessian(U n,U d,const double*x,const std::vector<double>&w,double lambda,std::vector<double>&H){
 U q=d+1;H.assign(q*q,0);std::vector<double>v(q,1);
 for(U i=0;i<n;i++){double z=w[0];for(U j=0;j<d;j++){v[j+1]=x[i*d+j];z+=w[j+1]*v[j+1];}if(!std::isfinite(z))return -3;double p=sigmoid(z),c=p*(1-p);for(U a=0;a<q;a++)for(U b=0;b<=a;b++)H[a*q+b]+=c*v[a]*v[b];}
 for(U a=0;a<q;a++)for(U b=0;b<=a;b++){double value=H[a*q+b]/n+(a==b&&a?lambda:0);if(!std::isfinite(value))return -3;H[a*q+b]=H[b*q+a]=value;}return 0;
}
static bool solve_cholesky(U q,const std::vector<double>&H,const std::vector<double>&g,std::vector<double>&delta){
 std::vector<double>L(q*q,0),v(q);
 for(U i=0;i<q;i++)for(U j=0;j<=i;j++){double a=H[i*q+j];for(U k=0;k<j;k++)a-=L[i*q+k]*L[j*q+k];if(i==j){if(!(a>0)||!std::isfinite(a))return false;L[i*q+j]=std::sqrt(a);}else L[i*q+j]=a/L[j*q+j];}
 for(U i=0;i<q;i++){double a=g[i];for(U j=0;j<i;j++)a-=L[i*q+j]*v[j];v[i]=a/L[i*q+i];}
 delta.assign(q,0);for(U ii=q;ii>0;ii--){U i=ii-1;double a=v[i];for(U j=i+1;j<q;j++)a-=L[j*q+i]*delta[j];delta[i]=a/L[i*q+i];if(!std::isfinite(delta[i]))return false;}return true;
}
extern "C" int rc_logistic_hessian(U n,U d,const double*x,const double*y,double lambda,const double*weights,double*output){
 try{int rc=valid(n,d,x,y,lambda);if(rc)return rc;if(!weights||!output||d>256)return -1;std::vector<double>w(weights,weights+d+1),H;for(double a:w)if(!std::isfinite(a))return -2;rc=hessian(n,d,x,w,lambda,H);if(rc)return rc;std::copy(H.begin(),H.end(),output);return 0;}catch(...){return -9;}
}
extern "C" int rc_logistic_newton(U n,U d,const double*x,const double*y,double lambda,U max_iterations,U max_backtracks,double tolerance,double*weights,double*statistics,double*trace){
 try{int rc=valid(n,d,x,y,lambda);if(rc)return rc;if(!weights||!statistics||!trace||d>256||lambda<=0||max_iterations>10000||!max_backtracks||max_backtracks>1000||!std::isfinite(tolerance)||tolerance<=0)return -1;U pos=0;for(U i=0;i<n;i++)pos+=y[i]==1;if(!pos||pos==n)return -2;
 U q=d+1,steps=0,code=1;std::vector<double>w(q,0),g(q),H,delta,candidate(q),temporary(q),history;double first,last;rc=compute(n,d,x,y,lambda,w,g,&first);if(rc)return rc;
 for(U iteration=0;iteration<=max_iterations;iteration++){
  rc=compute(n,d,x,y,lambda,w,g,&last);if(rc)return rc;double inf=0;for(double a:g)inf=std::max(inf,std::abs(a));long double current=objective(n,d,x,y,lambda,w);if(!std::isfinite(current))return -3;history.insert(history.end(),{double(iteration),double(current),inf,0});
  if(inf<=tolerance){code=0;break;}if(iteration==max_iterations)break;
  rc=hessian(n,d,x,w,lambda,H);if(rc)return rc;if(!solve_cholesky(q,H,g,delta)){code=3;break;}long double dot=0;for(U j=0;j<q;j++)dot+=(long double)g[j]*delta[j];if(!(dot>0)||!std::isfinite(dot)){code=3;break;}
  double alpha=1;bool accepted=false;for(U trial=0;trial<max_backtracks;trial++,alpha*=.5){bool finite=true;for(U j=0;j<q;j++){candidate[j]=w[j]-alpha*delta[j];finite=finite&&std::isfinite(candidate[j]);}if(!finite)continue;long double proposed=objective(n,d,x,y,lambda,candidate);if(std::isfinite(proposed)&&proposed<=current-1e-4L*alpha*dot){accepted=true;break;}}
  if(!accepted){code=2;break;}history.back()=alpha;w=candidate;steps++;
 }
 rc=compute(n,d,x,y,lambda,w,g,&last);if(rc)return rc;double norm=0,inf=0;for(double a:g){norm+=a*a;inf=std::max(inf,std::abs(a));}if(!std::isfinite(norm))return -3;std::copy(w.begin(),w.end(),weights);statistics[0]=first;statistics[1]=last;statistics[2]=std::sqrt(norm);statistics[3]=inf;statistics[4]=steps;statistics[5]=history.size()/4;std::copy(history.begin(),history.end(),trace);return code;
 }catch(...){return -9;}
}
