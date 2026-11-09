#pragma once
#include "trial_legality_array.hpp"
namespace tileplace_hbm {
struct Occupant {std::uint32_t found,block_id,unit_id;};
// Validated placement has unique locations; unit_id belongs to canonical units.
inline Occupant occupancy_array(const Block* blocks,const Location* positions,
 std::uint64_t count,Location query){
 for(std::uint64_t i=0;i<count;++i)if(location_equal(positions[i],query))return {1,blocks[i].id,blocks[i].unit_id};
 return {0,0,0};
}
}
