#pragma once
#include "../wire_checks/occupancy_shape_words.hpp"
namespace tileplace_wire_enumeration {
struct Owners {std::uint32_t count,unit,status;};
// Classify translated destinations into zero, one, or multiple external owner units.
// Count saturates at two because native candidate enumeration rejects multiple owners.
// Canonical placement/unique unit members/backing capacities are host validated.
// Status 1 unknown moved block, 2 count scaling.
inline Owners owners(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint32_t* own_members,std::uint32_t own_count,const std::uint64_t* moves,std::uint32_t mc){
 Owners out{};if(bc>UINT64_MAX/8){out.status=2;return out;}
 for(std::uint32_t i=0;i<mc;++i)if(tileplace_wire_candidates::block_index(blocks,bc,std::uint32_t(moves[3ULL*i]))==bc){out.status=1;return out;}
 for(std::uint32_t i=0;i<mc;++i){std::uint32_t status;auto found=tileplace_wire_checks::occupant(blocks,positions,bc,moves+3ULL*i+1,status);if(!found.found)continue;bool own=false;for(std::uint32_t j=0;j<own_count;++j)own|=own_members[j]==found.block_id;if(own)continue;
 if(!out.count){out.count=1;out.unit=found.unit_id;}else if(out.unit!=found.unit_id)out.count=2;
 }return out;
}
}
