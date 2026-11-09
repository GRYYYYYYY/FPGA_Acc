#pragma once
#include "../hbm_abi/guard_array.hpp"
#include "../hbm_abi/pressure_array_core.hpp"
namespace tileplace_cost_array {
using namespace tileplace_hbm;
struct NetCostResult {std::uint64_t costs[3];std::uint32_t status,reserved;};
inline bool sum_cost(std::uint64_t& total,std::uint64_t value){if(value>UINT64_MAX-total)return false;total+=value;return true;}
// Host validates canonical records, endpoint membership and unique trial IDs.
// Status 1: CSR range, 2: unknown block, 3: arithmetic, 4: pressure query.
inline NetCostResult net_cost_array(Net net,const Block* blocks,const Location* positions,std::uint64_t block_count,
 const std::uint32_t* members,std::uint64_t member_count,const Connection* connections,std::uint64_t connection_count,
 const PrefixLine* lines,std::uint64_t line_count,const PrefixEntry* entries,std::uint64_t entry_count,
 const TrialMove* moves,std::uint32_t move_count){
 NetCostResult out{};std::uint64_t values[3]{};
 if(!valid_range(net.members,member_count)||!valid_range(net.connections,connection_count)){out.status=1;return out;}
 for(std::uint32_t i=0;i<move_count;++i)if(translation_index(blocks,block_count,moves[i].id)==block_count){out.status=2;return out;}
 Location low{},high{};
 for(std::uint64_t i=0;i<net.members.count;++i){Location p{};
  if(!guard_position(blocks,positions,block_count,moves,move_count,members[net.members.offset+i],p)){out.status=2;return out;}
  if(!i)low=high=p;
  if(p.x<low.x)low.x=p.x;
  if(p.y<low.y)low.y=p.y;
  if(p.x>high.x)high.x=p.x;
  if(p.y>high.y)high.y=p.y;
 }
 if(net.members.count)values[0]=root_distance(low,high);
 for(std::uint64_t i=0;i<net.connections.count;++i){const auto& c=connections[net.connections.offset+i];Location a{},b{};
  if(!guard_position(blocks,positions,block_count,moves,move_count,c.source,a)||!guard_position(blocks,positions,block_count,moves,move_count,c.sink,b)){out.status=2;return out;}
  auto distance=root_distance(a,b);
  if(c.weight&&distance>UINT64_MAX/c.weight){out.status=3;return out;}
  if(!sum_cost(values[1],distance*c.weight)){out.status=3;return out;}
  auto pressure=pressure_array_query(lines,line_count,entries,entry_count,{a,b});
  if(pressure.status){out.status=4;return out;}
  if(!sum_cost(values[2],pressure.minimum)){out.status=3;return out;}
 }
 for(unsigned i=0;i<3;++i)out.costs[i]=values[i];
 return out;
}
}
