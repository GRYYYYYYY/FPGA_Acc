#include <cstdint>
using U=uint64_t;using W=__uint128_t;
extern "C" int rc_check(U n,U source,U initial,U clip,U clip_high,const U* row,const U* dst,const U* sw,const U* inc,const U* cap,const U* occ,const U* parent_src,const U* parent_sw,const U* pot,const U* present,U* checks){
 if(source>=n||clip_high>1||(clip_high&&clip))return -1;
 W c=clip_high?(W(1)<<64):W(clip);*checks=0;
 W start=present[source]?W(pot[source]):c;
 if(start!=(W(initial)<c?W(initial):c))return 1;
 for(U u=0;u<n;++u){
  if(!present[u])continue;
  W a=pot[u];if(a>=c||!cap[u])return 2;
  for(U e=row[u];e<row[u+1];++e){
   U v=dst[e];if(v>=n)return -1;
   if(occ[v]>=cap[v]||(parent_src[v]&&(parent_src[v]!=u+1||parent_sw[v]!=sw[e]+1)))continue;
   ++*checks;W b=present[v]?W(pot[v]):c;
   if(b>a+W(inc[e]))return 3;
  }
 }
 return 0;
}
