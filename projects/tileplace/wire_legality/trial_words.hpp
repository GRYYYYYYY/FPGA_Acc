#pragma once
#include "../wire_costs/net_cost_words.hpp"
namespace tileplace_wire_legality {
using namespace tileplace_hbm;
inline bool equal(Location a,Location b){return a.x==b.x&&a.y==b.y&&a.subtile==b.subtile&&a.layer==b.layer;}
inline bool less(Location a,Location b){if(a.x!=b.x)return a.x<b.x;if(a.y!=b.y)return a.y<b.y;if(a.subtile!=b.subtile)return a.subtile<b.subtile;return a.layer<b.layer;}
// External words follow snapshot ABI; trial is ID+two location words.
// Host validates canonical sorting, full placement and backing capacities.
inline bool trial(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint64_t* sites,std::uint64_t sc,const std::uint64_t* regions,std::uint64_t rc,const std::uint64_t* moves,std::uint32_t mc,std::uint32_t& status){
 status=0;if(bc>UINT64_MAX/8||sc>UINT64_MAX/4||rc>UINT64_MAX/4){status=3;return false;}
 for(std::uint32_t i=0;i<mc;++i){auto id=std::uint32_t(moves[3ULL*i]);auto p=tileplace_wire_costs::location(moves+3ULL*i+1);
  for(std::uint32_t j=0;j<i;++j){if(std::uint32_t(moves[3ULL*j])==id){status=1;return false;}if(equal(p,tileplace_wire_costs::location(moves+3ULL*j+1)))return false;}
  std::uint64_t low=0,high=bc;while(low<high){auto mid=low+(high-low)/2;if(std::uint32_t(blocks[8*mid])<id)low=mid+1;else high=mid;}
  if(low==bc||std::uint32_t(blocks[8*low])!=id){status=1;return false;}
  auto b=blocks+8*low;auto type=std::uint32_t(b[0]>>32),mask=std::uint32_t(b[7]);auto offset=b[3],count=b[4];
  if(offset>rc||count>rc-offset){status=2;return false;}
  low=0;high=sc;while(low<high){auto mid=low+(high-low)/2;if(less(tileplace_wire_costs::location(sites+4*mid),p))low=mid+1;else high=mid;}
  if(low==sc||!equal(tileplace_wire_costs::location(sites+4*low),p)||std::uint32_t(sites[4*low+2])!=type)return false;
  for(std::uint64_t j=0;j<bc;++j)if(equal(tileplace_wire_costs::location(positions+2*j),p)){bool moved=false;for(std::uint32_t k=0;k<mc;++k)moved|=std::uint32_t(moves[3ULL*k])==std::uint32_t(blocks[8*j]);if(!moved)return false;}
  if(mask&0x80000000u){bool inside=false;for(std::uint64_t j=0;j<count;++j){auto r=regions+4*(offset+j);auto xymin=tileplace_wire_costs::location(r);auto z=tileplace_wire_costs::location(r+2);
   inside|=xymin.x<=p.x&&p.x<=xymin.subtile&&xymin.y<=p.y&&p.y<=xymin.layer&&z.x<=p.layer&&p.layer<=z.y&&(z.subtile==-1||z.subtile==p.subtile);
  }if(!inside)return false;}
  auto fixed=tileplace_wire_costs::location(b+5);std::int32_t target[4]={p.x,p.y,p.subtile,p.layer},values[4]={fixed.x,fixed.y,fixed.subtile,fixed.layer};for(unsigned j=0;j<4;++j)if((mask&(1u<<j))&&target[j]!=values[j])return false;
 }
 return true;
}
}
