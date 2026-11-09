#include "query_cost_frame.h"
#include "vpr_types.h"
#include "vtr_vector.h"
#include <cassert>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <tuple>
using Bank=vtr::vector<RRNodeId,t_rr_node_route_inf>;
struct View {
    Bank* bank;explicit View(Bank& b):bank(&b) {}
    size_t size() const noexcept {return bank->size();}
    const void* identity() const noexcept {return bank;}
    float& word(size_t n) const noexcept {return (*bank)[RRNodeId(n)].acc_cost;}
};
struct AliasView:View {using View::View;};
using Frame=routecast_v2::QueryCostFrame<View>;
using Claim=routecast_v2::FrameClaim;
static uint64_t rejected=0,cycles=0,neighbor_updates=0;
template<class F> void reject(F f) {bool caught=false;try {f();}catch(const routecast_v2::FrameError&) {caught=true;}assert(caught);++rejected;}
struct Image {
    size_t edge;uint32_t acc,path,back,up;short occ;
    bool operator==(const Image& b) const {return std::tie(edge,acc,path,back,up,occ)==std::tie(b.edge,b.acc,b.path,b.back,b.up,b.occ);}
};
static uint32_t raw(const float& v) {uint32_t r;std::memcpy(&r,&v,4);return r;}
static Image image(const t_rr_node_route_inf& r) {return {size_t(r.prev_edge),raw(r.acc_cost),raw(r.path_cost),raw(r.backward_path_cost),raw(r.R_upstream),r.occ()};}
static std::vector<Image> images(const Bank& b) {std::vector<Image> out;for(size_t n=0;n<b.size();++n)out.push_back(image(b[RRNodeId(n)]));return out;}
static void initialize(Bank& b,size_t n) {
    b.resize(n);
    for(size_t i=0;i<n;++i) {auto& r=b[RRNodeId(i)];r.prev_edge=RREdgeId(i+31);r.acc_cost=2.f+float(i%37)/16.f;r.path_cost=float(i%1024)/8.f;r.backward_path_cost=float(i%513)/4.f;r.R_upstream=float(i%511)/2.f;r.set_occ(i%7);}
}
static void mutate_neighbor(t_rr_node_route_inf& r) {
    r.prev_edge=RREdgeId(size_t(r.prev_edge)+1);r.path_cost+=0.25f;r.backward_path_cost+=0.5f;r.R_upstream+=0.75f;r.set_occ((r.occ()+1)%19);++neighbor_updates;
}
static void check_cycle(Frame& frame,Bank& bank,uint32_t net,uint32_t iteration,bool enabled) {
    auto expected=images(bank);auto token=frame.begin(17,net,iteration,enabled);
    if(enabled && iteration==1)for(const auto& c:frame.claims_for(net))expected[c.node].acc=Frame::one_bits;
    assert(images(bank)==expected);
    // A real search is allowed to update occupancy and all path fields, including claimed nodes.
    mutate_neighbor(bank[RRNodeId(net%bank.size())]);
    for(const auto& c:frame.claims_for(net))mutate_neighbor(bank[RRNodeId(c.node)]);
    expected=images(bank);
    if(enabled && iteration==1)for(const auto& c:frame.claims_for(net))expected[c.node].acc=c.hint_bits;
    frame.finish(token);assert(images(bank)==expected);++cycles;
}
static void synthetic() {
    std::mt19937 rng(20261019);
    for(unsigned trial=0;trial<2000;++trial) {
        Bank bank;initialize(bank,1+rng()%64);uint32_t nets=1+rng()%8;View view(bank);std::vector<Claim> claims;
        for(uint32_t n=0;n<bank.size();++n)if(rng()%3==0)claims.push_back({n,uint32_t(rng()%nets),raw(bank[RRNodeId(n)].acc_cost)});
        Frame frame(view,nets,17,claims);
        for(uint32_t net=0;net<nets;++net) {check_cycle(frame,bank,net,1,true);check_cycle(frame,bank,net,1,false);check_cycle(frame,bank,net,2,true);}
        auto before=images(bank);auto token=frame.begin(17,0,1);auto active=images(bank);reject([&]{frame.begin(17,0,1);});auto stale=token;++stale.epoch;reject([&]{frame.finish(stale);});assert(images(bank)==active);frame.finish(token);assert(images(bank)==before);reject([&]{frame.finish(token);});reject([&]{frame.begin(18,0,1);});reject([&]{frame.begin(17,nets,1);});
        AliasView alias(bank);reject([&]{routecast_v2::QueryCostFrame<AliasView> duplicate(alias,nets,17,claims);});assert(images(bank)==before);
    }
    { Bank bank;initialize(bank,3);View v(bank);Frame f(v,1,17,{{0,0,raw(bank[RRNodeId(0)].acc_cost)}});std::vector<Image> expected;
      try {auto s=f.scoped(17,0,1);mutate_neighbor(bank[RRNodeId(0)]);expected=images(bank);expected[0].acc=routecast_v2::cost_bits(2.f);throw std::runtime_error("search exception");}catch(const std::runtime_error&){}assert(images(bank)==expected && !f.active());
      auto early=[&](){auto s=f.scoped(17,0,1);mutate_neighbor(bank[RRNodeId(0)]);expected=images(bank);expected[0].acc=routecast_v2::cost_bits(2.f);return false;};assert(!early() && images(bank)==expected && !f.active());
    }
    { Bank a,b;initialize(a,3);initialize(b,3);View va(a);AliasView vb(b);Frame fa(va,1,17,{{0,0,raw(a[RRNodeId(0)].acc_cost)}});routecast_v2::QueryCostFrame<AliasView> fb(vb,1,17,{{0,0,raw(b[RRNodeId(0)].acc_cost)}});auto ta=fa.begin(17,0,1),tb=fb.begin(17,0,1);auto ia=images(a),ib=images(b);reject([&]{fa.finish(tb);});assert(images(a)==ia && images(b)==ib);va.bank=&b;reject([&]{fa.finish(ta);});assert(images(a)==ia && images(b)==ib);va.bank=&a;fa.finish(ta);fb.finish(tb); }
    { Bank a;initialize(a,3);View v(a);auto hint0=raw(a[RRNodeId(0)].acc_cost),hint2=raw(a[RRNodeId(2)].acc_cost);Frame f(v,1,17,{{0,0,hint0},{2,0,hint2}});a[RRNodeId(2)].acc_cost=7.f;auto before=images(a);reject([&]{f.begin(17,0,1);});assert(images(a)==before && !f.active()); }
    { Bank a;initialize(a,3);View v(a);Frame f(v,1,17,{{0,0,raw(a[RRNodeId(0)].acc_cost)}});auto token=f.begin(17,0,1);a.resize(4);auto altered=images(a);reject([&]{f.finish(token);});assert(images(a)==altered);a.resize(3);f.finish(token); }
    { Bank a;initialize(a,3);View v(a);Frame f(v,1,17,{});auto t=f.begin(17,0,1);a[RRNodeId(1)].acc_cost=9.5f;mutate_neighbor(a[RRNodeId(1)]);auto expected=images(a);f.finish(t);assert(images(a)==expected); }
    for(auto config: {std::pair<bool,uint32_t>{false,1},{true,2}}) {Bank a;initialize(a,3);View v(a);Frame f(v,1,17,{{0,0,raw(a[RRNodeId(0)].acc_cost)}},config.first,config.second);auto before=images(a);reject([&]{f.begin(17,0,1);});assert(images(a)==before);auto t=f.begin(17,0,2);f.finish(t);assert(images(a)==before);}
    std::cout<<"NATIVE_TYPED_ACCESSOR_PASS "<<cycles<<" "<<rejected<<" "<<neighbor_updates<<" sizeof_record="<<sizeof(t_rr_node_route_inf)<<"\n";
}
static void history_fault() {
    Bank bank;initialize(bank,3);View view(bank);Frame f(view,1,17,{{0,0,raw(bank[RRNodeId(0)].acc_cost)},{2,0,raw(bank[RRNodeId(2)].acc_cost)}});auto token=f.begin(17,0,1);mutate_neighbor(bank[RRNodeId(0)]);mutate_neighbor(bank[RRNodeId(2)]);bank[RRNodeId(2)].acc_cost=1.5f;auto changed=images(bank);reject([&]{f.finish(token);});assert(images(bank)==changed && f.active());reject([&]{f.begin(17,0,1);});std::cout<<"NATIVE_TYPED_UNEXPECTED_HISTORY_AND_NEIGHBORS_PRESERVED\n"<<std::flush;std::_Exit(86);
}
int main(int argc,char** argv) {
    if(argc==2 && std::string(argv[1])=="--history-fault") {history_fault();return 1;}
    synthetic();return 0;
}
