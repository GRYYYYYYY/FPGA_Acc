#pragma once
#include "macro_translation_array.hpp"
namespace tileplace_hbm {
inline bool macro_shape_array(const Block* blocks,const Location* positions,std::uint64_t count,
 const std::uint32_t* a,std::uint32_t na,const std::uint32_t* b,std::uint32_t nb,std::uint32_t& status){
 status=0;if(!na||!nb){status=1;return false;}if(na!=nb)return false;
 auto ar=translation_index(blocks,count,a[0]),br=translation_index(blocks,count,b[0]);
 if(ar==count||br==count){status=2;return false;}
 // Host canonical units have unique members and unique positions, so each
 // typed four-dimensional relative location can match at most once.
 for(std::uint32_t i=0;i<na;++i)if(translation_index(blocks,count,a[i])==count||translation_index(blocks,count,b[i])==count){status=2;return false;}
 for(std::uint32_t i=0;i<na;++i){auto ai=translation_index(blocks,count,a[i]);bool found=false;
  auto p=positions[ai],root=positions[ar];
  for(std::uint32_t j=0;j<nb;++j){auto bi=translation_index(blocks,count,b[j]);auto q=positions[bi],other=positions[br];
   found|=blocks[ai].type_id==blocks[bi].type_id&&
    std::int64_t(p.x)-root.x==std::int64_t(q.x)-other.x&&std::int64_t(p.y)-root.y==std::int64_t(q.y)-other.y&&
    std::int64_t(p.subtile)-root.subtile==std::int64_t(q.subtile)-other.subtile&&std::int64_t(p.layer)-root.layer==std::int64_t(q.layer)-other.layer;
  }
  if(!found)return false;
 }
 return true;
}
}
