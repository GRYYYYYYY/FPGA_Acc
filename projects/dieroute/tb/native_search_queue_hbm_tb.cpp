#include "native_search_hbm_queue.hpp"
#include <array>
#include <cassert>
#include <queue>
extern "C" void dieroute_native_search_queue_hbm(dieroute::NativeSearchQueueEntry*,const dieroute::NativeSearchQueueEntry*,dieroute::NativeSearchQueueEntry*,std::uint32_t*,std::uint32_t*,std::uint32_t,std::uint32_t);
using namespace dieroute;
struct Greater{bool operator()(const NativeSearchQueueEntry&a,const NativeSearchQueueEntry&b)const{return native_search_queue_less(b,a);}};
static bool same(const NativeSearchQueueEntry&a,const NativeSearchQueueEntry&b){return a.priority==b.priority&&a.cost==b.cost&&a.hops==b.hops&&a.node==b.node&&a.parent==b.parent;}
int main(){
 std::array<NativeSearchQueueEntry,1024> data{};std::uint32_t count=0,status=99;NativeSearchQueueEntry in{},out{9,8,7,6,5};
 std::priority_queue<NativeSearchQueueEntry,std::vector<NativeSearchQueueEntry>,Greater> golden;
 for(unsigned i=0;i<8;++i){in={7-i,i%3,i%2,8-i,i};dieroute_native_search_queue_hbm(data.data(),&in,&out,&count,&status,8,1);assert(status==0&&count==i+1);golden.push(in);}
 auto saved=data;dieroute_native_search_queue_hbm(data.data(),&in,&out,&count,&status,8,1);assert(status==1&&count==8);for(unsigned i=0;i<8;++i)assert(same(saved[i],data[i]));
 dieroute_native_search_queue_hbm(data.data(),&in,&out,&count,&status,8,7);assert(status==2&&count==8);
 for(unsigned i=0;i<8;++i){dieroute_native_search_queue_hbm(data.data(),&in,&out,&count,&status,8,2);assert(status==0&&count==7-i&&same(out,golden.top()));golden.pop();}
 auto old=out;dieroute_native_search_queue_hbm(data.data(),&in,&out,&count,&status,8,2);assert(status==1&&count==0&&same(old,out));
 dieroute_native_search_queue_hbm(data.data(),&in,&out,&count,&status,1025,1);assert(status==2&&count==0);
}
