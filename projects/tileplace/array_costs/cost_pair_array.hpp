#pragma once
#include "net_cost_array.hpp"
namespace tileplace_cost_array {
struct CostPairResult {std::uint64_t before[4],after[4];std::uint32_t status,reserved;};
// Host supplies canonical arrays and unique touched net IDs and trial IDs.
// Status 1: unknown net, 2: unknown block, 3: arithmetic, 4: pressure,
// 5: malformed net CSR. Results remain zero on any error.
inline CostPairResult cost_pair_array(const Net* nets,std::uint64_t net_count,
 const std::uint32_t* touched,std::uint32_t touched_count,
 const Block* blocks,const Location* positions,std::uint64_t block_count,
 const std::uint32_t* members,std::uint64_t member_count,
 const Connection* connections,std::uint64_t connection_count,
 const PrefixLine* lines,std::uint64_t line_count,const PrefixEntry* entries,std::uint64_t entry_count,
 const Connection* routed,std::uint64_t routed_count,const TrialMove* moves,std::uint32_t move_count){
 CostPairResult out{},values{};
 for(std::uint32_t i=0;i<move_count;++i)
  if(translation_index(blocks,block_count,moves[i].id)==block_count){out.status=2;return out;}
 for(std::uint32_t i=0;i<touched_count;++i){
  std::uint64_t low=0,high=net_count;
  while(low<high){auto mid=low+(high-low)/2;if(nets[mid].id<touched[i])low=mid+1;else high=mid;}
  if(low==net_count||nets[low].id!=touched[i]){out.status=1;return out;}
  auto a=net_cost_array(nets[low],blocks,positions,block_count,members,member_count,connections,connection_count,lines,line_count,entries,entry_count,nullptr,0);
  auto b=net_cost_array(nets[low],blocks,positions,block_count,members,member_count,connections,connection_count,lines,line_count,entries,entry_count,moves,move_count);
  if(a.status||b.status){auto status=a.status?a.status:b.status;out.status=status==1?5:status;return out;}
  for(unsigned k=0;k<3;++k){auto target=k==2?3:k;
   if(!sum_cost(values.before[target],a.costs[k])||!sum_cost(values.after[target],b.costs[k])){out.status=3;return out;}
  }
 }
 for(std::uint64_t i=0;i<routed_count;++i){const auto& c=routed[i];bool changed=false;
  for(std::uint32_t j=0;j<move_count;++j)if(moves[j].id==c.source||moves[j].id==c.sink)changed=true;
  if(!changed)continue;
  Location a{},b{},x{},y{};
  if(!guard_position(blocks,positions,block_count,nullptr,0,c.source,a)||!guard_position(blocks,positions,block_count,nullptr,0,c.sink,b)||
     !guard_position(blocks,positions,block_count,moves,move_count,c.source,x)||!guard_position(blocks,positions,block_count,moves,move_count,c.sink,y)){out.status=2;return out;}
  auto d=root_distance(a,b),e=root_distance(x,y);
  if(c.weight&&(d>UINT64_MAX/c.weight||e>UINT64_MAX/c.weight)){out.status=3;return out;}
  if(!sum_cost(values.before[2],d*c.weight)||!sum_cost(values.after[2],e*c.weight)){out.status=3;return out;}
 }
 return values;
}
}
