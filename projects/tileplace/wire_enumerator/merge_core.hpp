#pragma once
#include <cstdint>
namespace tileplace_wire_enumerator_merge {
// Merge two ID-sorted trial streams. On duplicate ID retain first stream,
// matching std::map::insert used for macro swaps. Host backs distinct buffers.
// Status 1 invalid ID ordering/width, 2 output capacity. Validation is atomic.
inline std::uint32_t merge(const std::uint64_t* a,std::uint32_t na,const std::uint64_t* b,std::uint32_t nb,std::uint64_t* out,std::uint32_t capacity,std::uint32_t& status){
 status=0;for(unsigned stream=0;stream<2;++stream){auto p=stream?b:a;auto n=stream?nb:na;for(std::uint32_t i=0;i<n;++i)if(p[3ULL*i]>UINT32_MAX||(i&&p[3ULL*i]<=p[3ULL*(i-1)])){status=1;return 0;}}
 std::uint32_t i=0,j=0;std::uint64_t count=0;
 while(i<na&&j<nb){auto x=a[3ULL*i],y=b[3ULL*j];if(x<y)++i;else if(y<x)++j;else{++i;++j;}++count;}
 count+=std::uint64_t(na-i)+nb-j;if(count>capacity){status=2;return 0;}
 i=j=0;std::uint32_t size=0;
 while(i<na&&j<nb){auto x=a[3ULL*i],y=b[3ULL*j];if(x<=y){out[3ULL*size]=a[3ULL*i];out[3ULL*size+1]=a[3ULL*i+1];out[3ULL*size+2]=a[3ULL*i+2];++i;if(x==y)++j;}else{out[3ULL*size]=b[3ULL*j];out[3ULL*size+1]=b[3ULL*j+1];out[3ULL*size+2]=b[3ULL*j+2];++j;}++size;}
 while(i<na){out[3ULL*size]=a[3ULL*i];out[3ULL*size+1]=a[3ULL*i+1];out[3ULL*size+2]=a[3ULL*i+2];++i;++size;}
 while(j<nb){out[3ULL*size]=b[3ULL*j];out[3ULL*size+1]=b[3ULL*j+1];out[3ULL*size+2]=b[3ULL*j+2];++j;++size;}
 return size;
}
}
