#include <cstdint>
#include <limits>
#include <vector>
using U=uint64_t;
static constexpr U MAX=std::numeric_limits<U>::max();
static int dimensions(U n,const U* cards,U nf,const U* strides,const U* lengths,const U* const* factors,U cells,U& total) {
 if(!n||!cards||(nf&&(!strides||!lengths||!factors)))return -1;
 U count=1;
 for(U i=0;i<n;++i)if(!cards[i])return -1;
 for(U i=1;i<n;++i){if(count>MAX/cards[i])return -2;count*=cards[i];}
 if(cells!=count||cells>MAX/cards[0])return -2;total=cells*cards[0];
 for(U f=0;f<nf;++f){
  if(!lengths[f]||!factors[f])return -3;U last=0;
  for(U i=0;i<n;++i){U s=strides[f*n+i];if(s&&cards[i]-1>MAX/s)return -3;U part=(cards[i]-1)*s;if(last>MAX-part)return -3;last+=part;}
  if(last>=lengths[f])return -3;
 }
 return 0;
}
// Producer enumerates separator rows, then each state of eliminated bag position0.
extern "C" int rc_min_sum(U n,const U* cards,U nf,const U* strides,const U* lengths,const U* const* factors,U cells,U* output,U* argmin) {
 try {
  if(!output||!argmin)return -1;U total;int valid=dimensions(n,cards,nf,strides,lengths,factors,cells,total);if(valid)return valid;
  std::vector<U> digit(n,0);
  for(U row=0;row<cells;++row){
   U rest=row;for(U k=n;k-->1;){digit[k]=rest%cards[k];rest/=cards[k];}
   bool have=false;U best=0,choice=0;
   for(U state=0;state<cards[0];++state){
    digit[0]=state;U score=0;
    for(U f=0;f<nf;++f){U index=0;for(U k=0;k<n;++k)index+=digit[k]*strides[f*n+k];U value=factors[f][index];if(score>MAX-value)return -4;score+=value;}
    if(!have||score<best){have=true;best=score;choice=state;}
   }
   output[row]=best;argmin[row]=choice;
  }
  return 0;
 }catch(...){return -9;}
}
// Checker instead enumerates every joint bag assignment and scatters minima.
extern "C" int rc_verify_min_sum(U n,const U* cards,U nf,const U* strides,const U* lengths,const U* const* factors,U cells,const U* output,const U* argmin) {
 try {
  if(!output||!argmin)return -1;U total;int valid=dimensions(n,cards,nf,strides,lengths,factors,cells,total);if(valid)return valid;
  std::vector<U> expected(cells,MAX),choices(cells,MAX),assignment(n,0);
  for(U joint=0;joint<total;++joint){
   U remaining=joint;
   for(U k=n;k-->0;){assignment[k]=remaining%cards[k];remaining/=cards[k];}
   U value=0;
   for(U f=0;f<nf;++f){U offset=0;for(U k=0;k<n;++k)offset+=strides[f*n+k]*assignment[k];U term=factors[f][offset];if(term>MAX-value)return -4;value+=term;}
   U row=joint%cells,state=assignment[0];
   if(value<expected[row]||(value==expected[row]&&state<choices[row])){expected[row]=value;choices[row]=state;}
  }
  for(U i=0;i<cells;++i)if(expected[i]!=output[i]||choices[i]!=argmin[i])return 1;
  return 0;
 }catch(...){return -9;}
}
