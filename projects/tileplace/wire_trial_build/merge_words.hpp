#pragma once
#include <cstdint>
namespace tileplace_wire_trial_build {
// Merge two ID-sorted trial streams. On duplicate ID retain first stream,
// matching std::map::insert used for macro swaps. Host backs distinct buffers.
// Status 1 invalid ID ordering/width, 2 output capacity. Validation is atomic.
inline std::uint32_t merge(const std::uint64_t* a,std::uint32_t na,const std::uint64_t* b,std::uint32_t nb,std::uint64_t* out,std::uint32_t capacity,std::uint32_t& status){
 status=0;for(unsigned stream=0;stream<2;++stream){auto p=stream?b:a;auto n=stream?nb:na;for(std::uint32_t i=0;i<n;++i)if(p[3ULL*i]>UINT32_MAX||(i&&p[3ULL*i]<=p[3ULL*(i-1)])){status=1;return 0;}}
 std::uint32_t i=0,j=0;std::uint64_t count=0;while(i<na||j<nb){if(j==nb||(i<na&&a[3ULL*i]<b[3ULL*j]))++i;else if(i==na||b[3ULL*j]<a[3ULL*i])++j;else{++i;++j;}++count;}if(count>capacity){status=2;return 0;}
 i=j=0;std::uint32_t size=0;while(i<na||j<nb){const std::uint64_t* p;if(j==nb||(i<na&&a[3ULL*i]<=b[3ULL*j])){p=a+3ULL*i;if(j<nb&&a[3ULL*i]==b[3ULL*j])++j;++i;}else{p=b+3ULL*j;++j;}for(unsigned k=0;k<3;++k)out[3ULL*size+k]=p[k];++size;}return size;
}
}
