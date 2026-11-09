#pragma once
#include "net_cost_words.hpp"
namespace tileplace_wire_costs {
struct CostPairResult {std::uint64_t before[4],after[4];std::uint32_t status,reserved;};
// Host supplies canonical arrays and unique touched net IDs and trial IDs.
// Status 1: unknown net, 2: unknown block, 3: arithmetic, 4: pressure,
// 5: malformed net CSR. Results remain zero on any error.
inline CostPairResult cost_pair_words(const std::uint64_t* nets,std::uint64_t net_count,
 const std::uint32_t* touched,std::uint32_t touched_count,
 const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t block_count,
 const std::uint32_t* members,std::uint64_t member_count,
 const std::uint64_t* connections,std::uint64_t connection_count,
 const std::uint64_t* lines,std::uint64_t line_count,const std::uint64_t* entries,std::uint64_t entry_count,
 const std::uint64_t* routed,std::uint64_t routed_count,const std::uint64_t* moves,std::uint32_t move_count){
 CostPairResult out{},values{};
 if(net_count>UINT64_MAX/6||block_count>UINT64_MAX/8||routed_count>UINT64_MAX/2){out.status=5;return out;}
 Location scratch{};
 for(std::uint32_t i=0;i<move_count;++i)
  if(!position(blocks,positions,block_count,moves,move_count,std::uint32_t(moves[3ULL*i]),scratch)){out.status=2;return out;}
 for(std::uint32_t i=0;i<touched_count;++i){
  std::uint64_t low=0,high=net_count;
  while(low<high){auto mid=low+(high-low)/2;if(std::uint32_t(nets[6*mid])<touched[i])low=mid+1;else high=mid;}
  if(low==net_count||std::uint32_t(nets[6*low])!=touched[i]){out.status=1;return out;}
  auto a=net_cost({nets[6*low+2],nets[6*low+3]},{nets[6*low+4],nets[6*low+5]},blocks,positions,block_count,members,member_count,connections,connection_count,lines,line_count,entries,entry_count,nullptr,0);
  auto b=net_cost({nets[6*low+2],nets[6*low+3]},{nets[6*low+4],nets[6*low+5]},blocks,positions,block_count,members,member_count,connections,connection_count,lines,line_count,entries,entry_count,moves,move_count);
  if(a.status||b.status){auto status=a.status?a.status:b.status;out.status=status==1?5:status;return out;}
  for(unsigned k=0;k<3;++k){auto target=k==2?3:k;
   if(!add(values.before[target],a.costs[k])||!add(values.after[target],b.costs[k])){out.status=3;return out;}
  }
 }
 for(std::uint64_t i=0;i<routed_count;++i){auto ids=routed[2*i],weight=routed[2*i+1];auto source=std::uint32_t(ids),sink=std::uint32_t(ids>>32);bool changed=false;
  for(std::uint32_t j=0;j<move_count;++j)if(std::uint32_t(moves[3ULL*j])==source||std::uint32_t(moves[3ULL*j])==sink)changed=true;
  if(!changed)continue;
  Location a{},b{},x{},y{};
  if(!position(blocks,positions,block_count,nullptr,0,source,a)||!position(blocks,positions,block_count,nullptr,0,sink,b)||
     !position(blocks,positions,block_count,moves,move_count,source,x)||!position(blocks,positions,block_count,moves,move_count,sink,y)){out.status=2;return out;}
  auto d=distance(a,b),e=distance(x,y);
  std::uint64_t wd=0,we=0;if(!product(d,weight,wd)||!product(e,weight,we)){out.status=3;return out;}
  if(!add(values.before[2],wd)||!add(values.after[2],we)){out.status=3;return out;}
 }
 return values;
}
}
