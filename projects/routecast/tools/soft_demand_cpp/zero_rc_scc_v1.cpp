#include <cstdint>
#include <vector>
#include <limits>
#include <algorithm>
using U=uint64_t;
extern "C" int zero_rc_scc(U n,const U* row,const U* dest,const U* inc,const U* cap,U* component,U* count){
 try{
  if(!n||!row||!dest||!inc||!cap||!component||!count||row[0])return -1;
  for(U u=0;u<n;++u){if(row[u]>row[u+1])return -1;for(U e=row[u];e<row[u+1];++e)if(dest[e]>=n)return -1;}
  const U none=std::numeric_limits<U>::max();
  std::vector<U> reverse_row(n+1,0),order;
  for(U u=0;u<n;++u)if(cap[u])for(U e=row[u];e<row[u+1];++e)if(!inc[e]&&cap[dest[e]])++reverse_row[dest[e]+1];
  for(U u=0;u<n;++u)reverse_row[u+1]+=reverse_row[u];
  auto next=reverse_row;std::vector<U> reverse_dest(reverse_row.back());
  for(U u=0;u<n;++u)if(cap[u])for(U e=row[u];e<row[u+1];++e)if(!inc[e]&&cap[dest[e]])reverse_dest[next[dest[e]]++]=u;
  std::vector<uint8_t> seen(n,0);std::vector<std::pair<U,U>> stack;
  for(U root=0;root<n;++root)if(cap[root]&&!seen[root]){
   seen[root]=1;stack.push_back({root,row[root]});
   while(!stack.empty()){
    U u=stack.back().first;auto& e=stack.back().second;
    while(e<row[u+1]&&(inc[e]||!cap[dest[e]]||seen[dest[e]]))++e;
    if(e==row[u+1]){order.push_back(u);stack.pop_back();}
    else{U v=dest[e++];seen[v]=1;stack.push_back({v,row[v]});}
   }
  }
  std::fill(component,component+n,none);U total=0;std::vector<U> todo;
  for(auto it=order.rbegin();it!=order.rend();++it)if(component[*it]==none){
   component[*it]=total;todo.push_back(*it);
   while(!todo.empty()){
    U u=todo.back();todo.pop_back();
    for(U e=reverse_row[u];e<reverse_row[u+1];++e){U v=reverse_dest[e];if(component[v]==none){component[v]=total;todo.push_back(v);}}
   }
   ++total;
  }
  *count=total;return 0;
 }catch(...){return -2;}
}
