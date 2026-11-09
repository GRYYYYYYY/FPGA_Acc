#include "native_net_transaction_strict.hpp"
#include <iostream>
using namespace dieroute;
void check(bool ok){if(!ok)throw std::runtime_error("strict SLL search invariant");}
int main(){
 auto member=[](std::uint32_t n){return n==2||n==4?3U:n==3||n==5||n==6?2U:1U;};
 auto allowed=[](auto,auto){return true;};auto edge=[](auto a,auto b,auto key){return key==a*10+b;};
 NativeRouteState state(NativeOwnerLayout::from_membership(2,member));state.start(0,0,allowed);state.start(1,7,allowed);
 SparseSearchResult held;held.status=SparseSearchStatus::found;held.attachment=7;held.path={2};held.edges={72};held.hops=1;state.accept(1,2,held,allowed,edge);
 std::map<std::uint32_t,std::vector<std::uint32_t>> arcs{{0,{2,4}},{2,{3}},{4,{5}},{5,{6}},{6,{3}}};
 auto expand=[&](auto n,auto emit){for(auto dst:arcs[n]){auto mask=member(n)&member(dst);std::uint32_t die=0;while(!(mask&(1U<<die)))++die;emit(dst,n*10+dst,die);}};
 NativeCorridorRouter corridor({{2,3,3},{4,3,3}},2,8,false,false,1,true,true);SparseSearch search;
 auto proposal=native_propose_net_strict_sll(std::make_shared<const NativeRouteState>(state),0,{{0,3,1}},1,8,100,corridor,search,expand,member,allowed,edge,[](auto,auto){},[](auto){return std::uint64_t(0);},[](auto,auto){return std::uint64_t(0);});
 check(proposal.branches.size()==1&&proposal.branches[0].result.status==SparseSearchStatus::found);
 check(proposal.branches[0].result.path==std::vector<std::uint32_t>({4,5,6,3}));
 check(std::binary_search(proposal.reads.begin(),proposal.reads.end(),2));
 check(native_validate_net(state,proposal,1).valid());state.ripup(1);
 auto validation=native_validate_net(state,proposal,1);check(!validation.valid()&&std::find(validation.conflicts.begin(),validation.conflicts.end(),2)!=validation.conflicts.end());
 std::cout<<"strict SLL search avoids occupancy and records rejected-resource reads\n";
}
