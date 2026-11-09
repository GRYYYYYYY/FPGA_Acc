#pragma once
#include "macro_translation_array.hpp"
#include "candidate_root_array.hpp"
namespace tileplace_hbm {
struct ArrayGuard {std::uint32_t source,sink;std::uint64_t maximum;};
inline bool guard_position(const Block* blocks,const Location* positions,std::uint64_t count,
 const TrialMove* moves,std::uint32_t move_count,std::uint32_t id,Location& out){
 auto index=translation_index(blocks,count,id);if(index==count)return false;
 out=positions[index];for(std::uint32_t i=0;i<move_count;++i)if(moves[i].id==id)out=moves[i].target;
 return true;
}
// Canonical blocks/current positions and unique trial IDs are host-validated.
inline bool guard_array(const Block* blocks,const Location* positions,std::uint64_t count,
 const TrialMove* moves,std::uint32_t move_count,const ArrayGuard* guards,std::uint64_t guard_count,std::uint32_t& status){
 status=0;
 for(std::uint32_t i=0;i<move_count;++i)if(translation_index(blocks,count,moves[i].id)==count){status=1;return false;}
 for(std::uint64_t i=0;i<guard_count;++i){bool changed=false;
  for(std::uint32_t j=0;j<move_count;++j)changed|=moves[j].id==guards[i].source||moves[j].id==guards[i].sink;
  if(!changed)continue;
  Location a{},b{};
  if(!guard_position(blocks,positions,count,moves,move_count,guards[i].source,a)||!guard_position(blocks,positions,count,moves,move_count,guards[i].sink,b)){status=2;return false;}
  if(root_distance(a,b)>guards[i].maximum)return false;
 }
 return true;
}
}
