#pragma once
#include "../wire_checks/occupancy_shape_words.hpp"
namespace tileplace_wire_pipeline {
struct WriteResult {std::uint32_t count,changed,status;};
inline bool point_less(tileplace_hbm::Location a,tileplace_hbm::Location b){if(a.x!=b.x)return a.x<b.x;if(a.y!=b.y)return a.y<b.y;if(a.subtile!=b.subtile)return a.subtile<b.subtile;return a.layer<b.layer;}
inline tileplace_hbm::Location write_point(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint64_t* moves,std::uint64_t index){auto i=index/2;if(index%2)return tileplace_wire_candidates::location(moves+3*i+1);auto bi=tileplace_wire_candidates::block_index(blocks,bc,std::uint32_t(moves[3*i]));return tileplace_wire_candidates::location(positions+2*bi);}
// Union of old and trial locations for ALL trial IDs, matching Proposal.write_sites.
// Validate before writing: status 1 unknown ID, 2 capacity, 3 scaling, 4 duplicate trial ID.
// Distinct buffers and canonical blocks/backing capacities are host prerequisites.
inline WriteResult write_sites(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint64_t* moves,std::uint32_t mc,std::uint64_t* output,std::uint32_t capacity){
 WriteResult out{};if(bc>UINT64_MAX/8){out.status=3;return out;}
 for(std::uint32_t i=0;i<mc;++i){auto id=std::uint32_t(moves[3ULL*i]);if(tileplace_wire_candidates::block_index(blocks,bc,id)==bc){out.status=1;return out;}for(std::uint32_t j=0;j<i;++j)if(std::uint32_t(moves[3ULL*j])==id){out.status=4;return out;}}
 std::uint64_t total=0;bool changed=false;
 for(std::uint64_t i=0;i<2ULL*mc;++i){auto p=write_point(blocks,positions,bc,moves,i);if(i%2)changed|=!tileplace_wire_checks::equal(p,write_point(blocks,positions,bc,moves,i-1));bool duplicate=false;for(std::uint64_t j=0;j<i;++j)duplicate|=tileplace_wire_checks::equal(p,write_point(blocks,positions,bc,moves,j));total+=!duplicate;}
 if(total>capacity){out.status=2;return out;}std::uint32_t size=0;
 for(std::uint64_t i=0;i<2ULL*mc;++i){auto p=write_point(blocks,positions,bc,moves,i);std::uint32_t j=0;while(j<size&&point_less(tileplace_wire_candidates::location(output+2ULL*j),p))++j;if(j<size&&tileplace_wire_checks::equal(p,tileplace_wire_candidates::location(output+2ULL*j)))continue;
 for(auto k=size;k>j;--k){output[2ULL*k]=output[2ULL*(k-1)];output[2ULL*k+1]=output[2ULL*(k-1)+1];}tileplace_wire_candidates::store(output+2ULL*j,p);++size;
 }out.count=size;out.changed=changed;return out;
}
}
