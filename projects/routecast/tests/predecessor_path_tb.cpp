#ifdef NDEBUG
#undef NDEBUG
#endif
#include "predecessor_path.hpp"
#include <array>
#include <cassert>
int main(){
 std::array<uint64_t,5> parents{{UINT64_MAX,0,1,2,3}},edges{{0,91,17,83,42}};
 auto parent=[&](uint64_t n){return parents[n];};auto edge=[&](uint64_t n){return edges[n];};
 uint64_t scratch[6],output[6]={77,77,77,77,77,77},length=99;
 auto run=[&](uint64_t n,uint64_t sc,uint64_t oc){return routecast::reconstruct_path(n,0,5,parent,edge,scratch,sc,output,oc,length);};
 assert(run(4,3,6)==routecast::PathStatus::capacity);assert(length==99&&output[0]==77);
 assert(run(4,6,3)==routecast::PathStatus::capacity);assert(length==99&&output[0]==77);
 assert(run(4,6,6)==routecast::PathStatus::ok);assert(length==4&&output[0]==91&&output[1]==17&&output[2]==83&&output[3]==42);
 auto accepted=std::array<uint64_t,6>{output[0],output[1],output[2],output[3],output[4],output[5]};
 parents[2]=3;assert(run(4,6,6)==routecast::PathStatus::invalid_parent);assert(length==4);
 for(unsigned i=0;i<6;++i)assert(output[i]==accepted[i]);
 parents[2]=999;assert(run(4,6,6)==routecast::PathStatus::invalid_parent);assert(length==4);
 assert(run(99,6,6)==routecast::PathStatus::invalid_parent);assert(length==4);
 assert(run(0,0,0)==routecast::PathStatus::ok);assert(length==0);
}
