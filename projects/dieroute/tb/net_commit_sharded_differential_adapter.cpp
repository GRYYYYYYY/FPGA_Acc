// Existing command suites drive both unchanged flat core and banked core.
#include "net_commit_sharded_hbm.hpp"
#include <vector>
#include <array>
#include <cstring>
#include <stdexcept>
#include <iostream>
#include <algorithm>
namespace dieroute {
extern "C" void dieroute_net_commit_flat_reference(const SummaryWord*,const std::uint64_t*,const std::uint64_t*,const std::uint64_t*,const std::uint64_t*,const SummaryWord*,const SummaryWord*,const std::uint64_t*,SummaryWord*,SummaryWord*,SummaryWord*,SummaryWord*,SummaryWord*,SummaryWord*,SummaryWord*,std::uint32_t,std::uint64_t,std::uint32_t,std::uint32_t,std::uint32_t,std::uint32_t,std::uint32_t,std::uint32_t,std::uint32_t,std::uint32_t,std::uint32_t,std::uint32_t);
namespace {
unsigned calls=0;
struct Count {~Count(){std::cout<<"SHARDED_DIFFERENTIAL calls="<<calls<<" isolated_owner_banks=3\n";}} count;
bool equal(const void* a,const void* b,std::size_t n){return !n||!std::memcmp(a,b,n);}
void require(bool ok){if(!ok)throw std::runtime_error("sharded/flat byte differential or owner guard failed");}
std::vector<SummaryWord> copy(const SummaryWord* p,std::size_t n){std::vector<SummaryWord> result(n);if(n)std::memcpy(result.data(),p,n*64);return result;}
}
extern "C" void dieroute_net_commit_hbm(
 const SummaryWord* command,const std::uint64_t* policy,const std::uint64_t* offsets,const std::uint64_t* arcs,
 const std::uint64_t* reads,const SummaryWord* shadows,const SummaryWord* branches,const std::uint64_t* paths,
 SummaryWord* resources,SummaryWord* trees,SummaryWord* nets,SummaryWord* control,SummaryWord* scratch,
 SummaryWord* deltas,SummaryWord* completion,
 std::uint32_t node_count,std::uint64_t arc_count,std::uint32_t dies,std::uint32_t shard_capacity,
 std::uint32_t net_capacity,std::uint32_t tree_capacity,std::uint32_t read_capacity,std::uint32_t shadow_capacity,
 std::uint32_t branch_capacity,std::uint32_t path_capacity,std::uint32_t scratch_capacity,std::uint32_t delta_capacity){
 require(dies<=3);auto flat=copy(resources,std::size_t(dies)*shard_capacity),tr=copy(trees,tree_capacity),nr=copy(nets,net_capacity),sc=copy(scratch,std::size_t(scratch_capacity)*2),dr=copy(deltas,delta_capacity);SummaryWord ctl=*control,done=*completion;
 constexpr unsigned guard=4;SummaryWord sentinel{};for(auto& w:sentinel.w)w=UINT64_C(0xa5912f73d26be048);
 const auto physical_capacity=std::max<std::uint32_t>(16,shard_capacity);
 std::array<std::vector<SummaryWord>,3> banks;for(unsigned owner=0;owner<3;++owner){banks[owner].assign(physical_capacity+guard*2,sentinel);if(owner<dies&&shard_capacity)std::memcpy(banks[owner].data()+guard,resources+std::size_t(owner)*shard_capacity,shard_capacity*64);}
 dieroute_net_commit_flat_reference(command,policy,offsets,arcs,reads,shadows,branches,paths,flat.data(),tr.data(),nr.data(),&ctl,sc.data(),dr.data(),&done,node_count,arc_count,dies,shard_capacity,net_capacity,tree_capacity,read_capacity,shadow_capacity,branch_capacity,path_capacity,scratch_capacity,delta_capacity);
 dieroute_net_commit_sharded_hbm(command,policy,offsets,arcs,reads,shadows,branches,paths,banks[0].data()+guard,banks[1].data()+guard,banks[2].data()+guard,trees,nets,control,scratch,deltas,completion,node_count,arc_count,dies,shard_capacity,net_capacity,tree_capacity,read_capacity,shadow_capacity,branch_capacity,path_capacity,scratch_capacity,delta_capacity);
 for(unsigned owner=0;owner<3;++owner){for(unsigned i=0;i<guard;++i){require(!std::memcmp(&banks[owner][i],&sentinel,64));require(!std::memcmp(&banks[owner][physical_capacity+guard+i],&sentinel,64));}for(unsigned i=shard_capacity;i<physical_capacity;++i)require(!std::memcmp(&banks[owner][guard+i],&sentinel,64));if(owner<dies&&shard_capacity){require(!std::memcmp(banks[owner].data()+guard,flat.data()+std::size_t(owner)*shard_capacity,shard_capacity*64));std::memcpy(resources+std::size_t(owner)*shard_capacity,banks[owner].data()+guard,shard_capacity*64);}else for(unsigned i=0;i<shard_capacity;++i)require(!std::memcmp(&banks[owner][guard+i],&sentinel,64));}
 require(equal(trees,tr.data(),tree_capacity*64));require(equal(nets,nr.data(),net_capacity*64));require(!std::memcmp(control,&ctl,64));require(equal(scratch,sc.data(),std::size_t(scratch_capacity)*128));require(equal(deltas,dr.data(),delta_capacity*64));require(!std::memcmp(completion,&done,64));++calls;
}
}
