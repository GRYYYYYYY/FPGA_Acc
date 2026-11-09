#include <cstdint>
using U=uint64_t;using I=uint32_t;using B=uint8_t;using W=unsigned __int128;
extern "C" int verify_raw_mask_dual(U n,U m,const I* us,const I* vs,const U* weight,const I* cap,const U* p,const B* cut,const B* blocked,U source,U initial,U cutoff,int require_cut,U* bad,U* checked){
 *bad=0;*checked=0;
 if(source>=n||!cap[source]||blocked[source]||!cut[source]||p[source]!=initial)return 1;
 for(U i=0;i<n;++i){
  if(p[i]>cutoff||cut[i]>1||blocked[i]>1){*bad=i;return 2;}
  if(cut[i]&&(!cap[i]||blocked[i])){*bad=i;return 3;}
 }
 for(U e=0;e<m;++e){
  U a=us[e],b=vs[e];if(a>=n||b>=n){*bad=e;return 6;}
  if(!cap[a]||!cap[b]||blocked[a]||blocked[b])continue;
  ++*checked;
  if(W(p[b])>W(p[a])+W(weight[e])){*bad=e;return 4;}
  if(require_cut&&cut[a]&&!cut[b]){*bad=e;return 5;}
 }
 return 0;
}
