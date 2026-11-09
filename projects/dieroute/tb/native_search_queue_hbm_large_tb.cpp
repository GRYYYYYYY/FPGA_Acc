#include "native_search_hbm_queue.hpp"
#include <array>
#include <cassert>
#include <queue>
#include <tuple>
#include <iostream>
extern "C" void dieroute_native_search_queue_hbm(dieroute::NativeSearchQueueEntry*,const dieroute::NativeSearchQueueEntry*,dieroute::NativeSearchQueueEntry*,std::uint32_t*,std::uint32_t*,std::uint32_t,std::uint32_t);
using namespace dieroute;
static auto key(const NativeSearchQueueEntry&e){return std::make_tuple(e.priority,e.cost,e.hops,e.node,e.parent);}
struct Greater{bool operator()(const NativeSearchQueueEntry&a,const NativeSearchQueueEntry&b)const{return key(a)>key(b);}};
int main(){
 std::array<NativeSearchQueueEntry,1024> data{};std::uint32_t count=0,status=99;NativeSearchQueueEntry input{},output{9,8,7,6,5};unsigned calls=0;
 std::priority_queue<NativeSearchQueueEntry,std::vector<NativeSearchQueueEntry>,Greater> golden;
 auto call=[&](unsigned op,unsigned cap){++calls;dieroute_native_search_queue_hbm(data.data(),&input,&output,&count,&status,cap,op);};
 auto push=[&](NativeSearchQueueEntry e){input=e;call(1,1024);assert(status==0);golden.push(e);assert(count==golden.size());};
 auto pop=[&](){call(2,1024);assert(status==0&&key(output)==key(golden.top()));golden.pop();assert(count==golden.size());};
 for(unsigned i=0;i<1024;++i)push({i%3,i%7,i%5,(i*13)%97,(i*19)%31});
 auto saved=data;call(1,1024);assert(status==1&&count==1024);for(unsigned i=0;i<1024;++i)assert(key(saved[i])==key(data[i]));
 for(unsigned i=0;i<128;++i){pop();push({i%3,i%7,i%5,(i*11)%97,(i*17)%31});}
 while(!golden.empty())pop();
 auto old=output;call(2,1024);assert(status==1&&count==0&&key(old)==key(output));
 call(1,0);assert(status==2&&count==0);call(7,1024);assert(status==2&&count==0);
 count=1025;saved=data;call(1,1024);assert(status==2&&count==1025);for(unsigned i=0;i<1024;++i)assert(key(saved[i])==key(data[i]));
 std::cout<<"RTL_COMPONENT_EXPECTED_CALLS="<<calls<<" capacity=1024\n";
}
