#ifdef NDEBUG
#undef NDEBUG
#endif
#include "direct_path.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <random>
#include <tuple>
#include <vector>
int main(){
 constexpr unsigned N=64;std::array<routecast::SearchLabel,N> labels;uint64_t left[N],right[N];std::mt19937_64 rng(731);
 for(unsigned trial=0;trial<150;++trial){
  labels[0]={0,0,UINT64_MAX,UINT64_MAX};std::vector<std::vector<uint64_t>> paths(N);
  for(unsigned n=1;n<N;++n){uint64_t parent=rng()%n,edge=rng()%7;labels[n]={rng()%4,rng()%4,parent,edge};paths[n]=paths[parent];paths[n].push_back(edge);}
  for(unsigned j=0;j<200;++j){uint64_t a=rng()%N,b=rng()%N;auto ka=std::make_tuple(labels[a].cost.high,labels[a].cost.low,labels[a].hops,paths[a],a);auto kb=std::make_tuple(labels[b].cost.high,labels[b].cost.low,labels[b].hops,paths[b],b);routecast::PathStatus status;int got=routecast::direct_label_compare(a,b,0,N,labels.data(),left,right,N,status);assert(status==routecast::PathStatus::ok);assert(got==(ka<kb?-1:(kb<ka?1:0)));}
 }
 labels[1]={0,1,0,91};labels[2]={0,1,0,92};routecast::PathStatus status;assert(routecast::direct_label_compare(1,2,0,N,labels.data(),left,right,0,status)==0);assert(status==routecast::PathStatus::capacity);
 labels[1].parent=1;uint64_t length;assert(routecast::direct_reverse_path(1,0,N,labels.data(),left,N,length)==routecast::PathStatus::invalid_parent);
 labels[1].parent=N;assert(routecast::direct_reverse_path(1,0,N,labels.data(),left,N,length)==routecast::PathStatus::invalid_parent);
}
