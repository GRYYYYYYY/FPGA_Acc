// Atomic per-NET union replacement. This component does not validate physical
// paths, budgets, parent consistency, or perform search; caller must do so.
#include <algorithm>
#include <cstdint>
#include <limits>
#include <map>
#include <memory>
#include <vector>
using U=uint64_t;
struct Net { U epoch; std::vector<U> nodes; };
struct Ledger { std::vector<U> cap,occ; std::map<U,Net> nets; };
static bool valid(const Ledger& l,const U* p,U n) {
 if(!p||!n)return false;
 for(U i=0;i<n;++i)if(p[i]>=l.cap.size()||(i&&p[i]<=p[i-1]))return false;
 return true;
}
extern "C" {
void* rc_ledger_create(const U* cap,U n) noexcept {
 try { if(!cap||!n)return nullptr;auto p=std::make_unique<Ledger>();
 p->cap.assign(cap,cap+n);p->occ.assign(n,0);return p.release(); }catch(...){return nullptr;}
}
void rc_ledger_free(void* p) noexcept {delete static_cast<Ledger*>(p);}
// Return 0 success, 1 invalid, 2 stale/unknown epoch, 3 retained overflow,
// 4 allocation/arithmetic failure. Failure never changes state or output delta.
int rc_ledger_add(void* p,U net,U epoch,const U* nodes,U n) noexcept {
 if(!p)return 1;auto& l=*static_cast<Ledger*>(p);
 if(!epoch||l.nets.count(net)||!valid(l,nodes,n))return 1;
 try {
  for(U i=0;i<n;++i)if(l.occ[nodes[i]]==std::numeric_limits<U>::max())return 4;
  Net v{epoch,std::vector<U>(nodes,nodes+n)};
  l.nets.emplace(net,std::move(v));
  for(U i=0;i<n;++i)++l.occ[nodes[i]];
  return 0;
 }catch(...){return 4;}
}
int rc_ledger_replace(void* p,U net,U expected,const U* nodes,U n,int64_t* delta) noexcept {
 if(!p||!delta)return 1;auto& l=*static_cast<Ledger*>(p);auto it=l.nets.find(net);
 if(it==l.nets.end()||it->second.epoch!=expected)return 2;
 if(expected==std::numeric_limits<U>::max()||!valid(l,nodes,n))return 1;
 try {
  // All allocation and arithmetic checks precede commit; swap cannot throw.
  std::vector<U> next(nodes,nodes+n),removed,added;
  const auto& old=it->second.nodes;
  std::set_difference(old.begin(),old.end(),next.begin(),next.end(),std::back_inserter(removed));
  std::set_difference(next.begin(),next.end(),old.begin(),old.end(),std::back_inserter(added));
  __int128 d=0;
  for(U x:removed){if(!l.occ[x])return 4;if(l.occ[x]>l.cap[x])--d;}
  for(U x:added){if(l.occ[x]==std::numeric_limits<U>::max())return 4;if(l.occ[x]>=l.cap[x])++d;}
  if(d<std::numeric_limits<int64_t>::min()||d>std::numeric_limits<int64_t>::max())return 4;
  *delta=static_cast<int64_t>(d);
  if(d>0)return 3;
  for(U x:removed)--l.occ[x];
  for(U x:added)++l.occ[x];
  it->second.nodes.swap(next);++it->second.epoch;return 0;
 }catch(...){return 4;}
}
int rc_ledger_export(void* p,U* occ,U n) noexcept {
 if(!p||!occ)return 1;const auto& l=*static_cast<Ledger*>(p);
 if(n!=l.occ.size())return 1;std::copy(l.occ.begin(),l.occ.end(),occ);return 0;
}
U rc_ledger_epoch(void* p,U net) noexcept {
 if(!p)return 0;auto& l=*static_cast<Ledger*>(p);auto i=l.nets.find(net);return i==l.nets.end()?0:i->second.epoch;
}
}
