#include <cstdint>
#include <vector>
#include <limits>
#include <algorithm>
using U=uint64_t;
extern "C" int rc_endpoint_full(U n,U m,const U*source,const U*sink,const U*base,U*output){
 try{
  if(!n||!base||!output||n>std::numeric_limits<U>::max()/15||n*15>std::numeric_limits<size_t>::max()/sizeof(U)||(m&&(!source||!sink)))return -1;
  for(U e=0;e<m;e++)if(source[e]>=n||sink[e]>=n)return -2;
  std::vector<U> values(n*15,0);
  for(U i=0;i<n;i++)for(U k=0;k<5;k++)values[i*15+k]=base[i*5+k];
  auto add=[&](U at,U value){if(values[at]>std::numeric_limits<U>::max()-value)return false;values[at]+=value;return true;};
  for(U hop=0;hop<2;hop++)for(U e=0;e<m;e++)for(U k=0;k<3;k++)if(!add(sink[e]*15+5+hop*3+k,values[source[e]*15+(hop?5:0)+k]))return -3;
  for(U hop=0;hop<2;hop++)for(U e=0;e<m;e++)for(U k=0;k<2;k++)if(!add(source[e]*15+11+hop*2+k,values[sink[e]*15+(hop?11:3)+k]))return -3;
  std::copy(values.begin(),values.end(),output);return 0;
 }catch(...){return -9;}
}
