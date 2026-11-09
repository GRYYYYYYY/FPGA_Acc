#pragma once
#include "snapshot_abi.hpp"
namespace tileplace_hbm {
struct TrialMove {std::uint32_t id;Location target;};
inline bool location_equal(Location a,Location b){return a.x==b.x&&a.y==b.y&&a.subtile==b.subtile&&a.layer==b.layer;}
inline bool location_less(Location a,Location b){
 if(a.x!=b.x)return a.x<b.x;
 if(a.y!=b.y)return a.y<b.y;
 if(a.subtile!=b.subtile)return a.subtile<b.subtile;
 return a.layer<b.layer;
}
// Host validates canonical sorted blocks/sites and complete current placement.
// Trial IDs define the moved set. Macro shape and guard checks remain separate.
inline bool trial_legality_array(const Block* blocks,const Location* positions,std::uint64_t block_count,
 const Site* sites,std::uint64_t site_count,const Region* regions,std::uint64_t region_count,
 const TrialMove* moves,std::uint32_t move_count,std::uint32_t& status){
 status=0;
 for(std::uint32_t i=0;i<move_count;++i){
  for(std::uint32_t j=0;j<i;++j){if(moves[i].id==moves[j].id){status=1;return false;}if(location_equal(moves[i].target,moves[j].target))return false;}
  std::uint64_t low=0,high=block_count;
  while(low<high){auto mid=low+(high-low)/2;if(blocks[mid].id<moves[i].id)low=mid+1;else high=mid;}
  if(low==block_count||blocks[low].id!=moves[i].id){status=1;return false;}
  const auto& b=blocks[low];auto target=moves[i].target;
  if(!valid_range(b.regions,region_count)){status=2;return false;}
  low=0;high=site_count;
  while(low<high){auto mid=low+(high-low)/2;if(location_less(sites[mid].location,target))low=mid+1;else high=mid;}
  if(low==site_count||!location_equal(sites[low].location,target)||sites[low].type_id!=b.type_id)return false;
  for(std::uint64_t j=0;j<block_count;++j)if(location_equal(positions[j],target)){
   bool moved=false;for(std::uint32_t k=0;k<move_count;++k)moved|=moves[k].id==blocks[j].id;
   if(!moved)return false;
  }
  if(b.fixed_mask&0x80000000u){bool inside=false;
   for(std::uint64_t j=0;j<b.regions.count;++j){const auto& r=regions[b.regions.offset+j];
    inside|=r.xmin<=target.x&&target.x<=r.xmax&&r.ymin<=target.y&&target.y<=r.ymax&&r.layer_low<=target.layer&&target.layer<=r.layer_high&&(r.subtile==-1||r.subtile==target.subtile);
   }
   if(!inside)return false;
  }
  std::int32_t values[4]={target.x,target.y,target.subtile,target.layer};
  for(unsigned j=0;j<4;++j)if((b.fixed_mask&(1u<<j))&&values[j]!=b.fixed[j])return false;
 }
 return true;
}
}
