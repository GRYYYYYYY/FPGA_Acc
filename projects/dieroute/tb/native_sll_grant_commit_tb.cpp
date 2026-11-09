#include "native_sll_grant_commit.hpp"
#include <iostream>
using namespace dieroute;
void check(bool ok){if(!ok)throw std::runtime_error("native SLL grant commit invariant");}
int main(){
 auto membership=[](std::uint32_t n){return n==2||n==4?3U:1U;};
 auto allowed=[](auto,auto){return true;};auto edge=[](auto a,auto b,auto key){return key==a*10+b;};
 NativeRouteState state(NativeOwnerLayout::from_membership(2,membership));state.start(0,0,allowed);state.start(1,1,allowed);NativeCapacityGrants grants;
 auto proposal=[&](std::uint32_t net,std::uint32_t source,std::uint32_t sink){NativeNetProposal p;p.net=net;p.present=1;p.snapshot=std::make_shared<const NativeRouteState>(state);p.reads={sink};SparseSearchResult r;r.status=SparseSearchStatus::found;r.attachment=source;r.path={sink};r.edges={source*10+sink};r.hops=state.tree(net).nodes.at(source).depth+1;r.cost=state.cost(sink,net,1);p.branches.push_back({{net,sink,0},0,false,false,r});return p;};
 auto p=proposal(0,0,2);check(native_proposal_sll_union(state,p)==std::vector<std::uint32_t>{2});
 auto commit=[&](const auto& p){return native_strict_sll_commit(grants,state,p,1,[&](const NativeNetProposal& granted){return native_commit_net(state,granted,1,allowed,edge);});};
 check(commit(p).committed&&grants.active()==0&&state.use(2).nets==std::set<std::uint32_t>{0});
 auto denied=proposal(1,1,2);auto revision=state.revision();auto result=commit(denied);check(!result.committed&&result.grant_status==NativeGrantStatus::capacity&&state.revision()==revision&&grants.active()==0);
 auto shared=proposal(0,2,3);check(native_proposal_sll_union(state,shared)==std::vector<std::uint32_t>{2});check(commit(shared).committed&&state.use(2).nets.size()==1&&grants.active()==0);
 auto bad=proposal(1,1,4);bad.branches[0].result.edges={999};revision=state.revision();bool threw=false;try{commit(bad);}catch(const std::logic_error&){threw=true;}check(threw&&grants.active()==0&&state.revision()==revision&&!state.find_use(4));
 state.ripup(0);auto fresh=proposal(1,1,2);check(commit(fresh).committed&&grants.active()==0&&state.use(2).nets==std::set<std::uint32_t>{1});
 // An outstanding tentative hold blocks another net before publication.
 auto observe=[&](auto n){NativeGrantObservation o;auto use=state.find_use(n);if(use){o.nets=use->nets;o.version=use->version;}return o;};
 auto hold=grants.acquire(9,{4},observe);check(hold.status==NativeGrantStatus::granted);
 auto held=proposal(0,0,4);bool dispatched=false;revision=state.revision();
 auto blocked=native_strict_sll_commit(grants,state,held,1,[&](const NativeNetProposal&){dispatched=true;return true;});
 check(blocked.grant_status==NativeGrantStatus::capacity&&!blocked.committed&&!dispatched&&state.revision()==revision&&grants.active()==1);
 check(grants.release(hold.handle,9)==NativeGrantStatus::released);check(commit(held).committed&&grants.active()==0);
 // A stale whole-net proposal must not dispatch or leak a grant.
 dispatched=false;auto stale=native_strict_sll_commit(grants,state,held,1,[&](const NativeNetProposal&){dispatched=true;return true;});
 check(stale.grant_status==NativeGrantStatus::stale&&!dispatched&&grants.active()==0);
 std::cout<<"native whole-net SLL grant/commit integration checks passed\n";
}
