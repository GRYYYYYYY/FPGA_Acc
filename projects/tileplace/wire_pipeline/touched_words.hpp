#pragma once
#include <cstdint>
namespace tileplace_wire_pipeline {
// Net ABI: six words, member offset/count at words 2/3; trial ID at word 0 of three.
// Output native net IDs in canonical net order. Host validates backing, IDs and disjoint buffers.
// Status 1: malformed member range; 2: output capacity; 3: record scaling.
inline bool affected(const std::uint64_t* net,const std::uint32_t* members,const std::uint64_t* moves,std::uint32_t size){for(std::uint64_t j=0;j<net[3];++j)for(std::uint32_t k=0;k<size;++k)if(members[net[2]+j]==std::uint32_t(moves[3ULL*k]))return true;return false;}
inline std::uint32_t touched(const std::uint64_t* nets,std::uint64_t count,const std::uint32_t* members,std::uint64_t mc,const std::uint64_t* moves,std::uint32_t size,std::uint32_t* output,std::uint32_t capacity,std::uint32_t& status){
 status=0;if(count>UINT64_MAX/6){status=3;return 0;}
 for(std::uint64_t i=0;i<count;++i){auto n=nets+6*i;if(n[2]>mc||n[3]>mc-n[2]){status=1;return 0;}}
 std::uint64_t total=0;for(std::uint64_t i=0;i<count;++i)total+=affected(nets+6*i,members,moves,size);if(total>capacity){status=2;return 0;}
 std::uint32_t out=0;for(std::uint64_t i=0;i<count;++i)if(affected(nets+6*i,members,moves,size))output[out++]=std::uint32_t(nets[6*i]);return out;
}
}
