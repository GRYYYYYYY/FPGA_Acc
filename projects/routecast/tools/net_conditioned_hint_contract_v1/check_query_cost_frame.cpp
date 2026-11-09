#include "query_cost_frame.h"
#include <cassert>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
using routecast::QueryCostFrame;using routecast::FrameError;
using Claim=QueryCostFrame::Claim;
static uint64_t checks=0,transactions=0;
static std::vector<uint32_t> bits(const std::vector<float>& a) {
    std::vector<uint32_t> r(a.size());if(!a.empty())std::memcpy(r.data(),a.data(),a.size()*4);return r;
}
template<class F> static void reject(F f) { bool caught=false;try {f();}catch(const FrameError&) {caught=true;}assert(caught);++checks; }
static void synthetic() {
    std::mt19937 rng(20261019);
    for(unsigned trial=0;trial<2000;++trial) {
        const uint32_t n=1+rng()%96,nets=1+rng()%8;std::vector<float> a(n);
        for(auto& x:a)x=1.f+float(rng()%1000)/16.f;
        std::vector<Claim> claims;
        for(uint32_t i=0;i<n;++i)if(rng()%3==0) {float h=1.f+float(1+rng()%160)/16.f;a[i]=h;claims.push_back({i,uint32_t(rng()%nets),routecast::cost_bits(h)});}
        const auto original=bits(a);QueryCostFrame frames(a,nets,17,claims);
        for(uint32_t net=0;net<nets;++net) {
            auto expected=original;for(const auto& c:claims)if(c.net==net)expected[c.node]=QueryCostFrame::one_bits;
            auto token=frames.begin(17,net,1);assert(bits(a)==expected);frames.finish(token);assert(bits(a)==original);++transactions;
            for(auto mode: {std::pair<uint32_t,bool>{1,false},{2,true}}) {
                auto t=frames.begin(17,net,mode.first,mode.second);assert(bits(a)==original);frames.finish(t);assert(bits(a)==original);++transactions;
            }
        }
        auto t=frames.begin(17,0,1);auto active=bits(a);reject([&]{frames.begin(17,0,1);});assert(bits(a)==active);
        auto stale=t;++stale.generation;reject([&]{frames.finish(stale);});assert(bits(a)==active && frames.active());frames.finish(t);
        reject([&]{frames.finish(t);});reject([&]{frames.begin(18,0,1);});reject([&]{frames.begin(17,nets,1);});reject([&]{frames.begin(17,0,0);});assert(bits(a)==original && !frames.active());
        reject([&]{QueryCostFrame duplicate(a,nets,17,claims);});
        if(!claims.empty()) {
            auto c=claims.front();routecast::set_cost_bits(a[c.node],c.hint_bits^1u);auto altered=bits(a);
            reject([&]{frames.begin(17,c.net,1);});assert(bits(a)==altered && !frames.active());
        }
    }
    { std::vector<float> a{2.f,3.f};QueryCostFrame f(a,1,1,{{0,0,routecast::cost_bits(2.f)}});auto t=f.begin(1,0,1);a[1]=9.25f;f.finish(t);assert(a[0]==2.f && a[1]==9.25f); }
    { std::vector<float> a{2.f,0.f,0.f,0.f};routecast::set_cost_bits(a[1],0x7fc01234);routecast::set_cost_bits(a[2],0x80000000);routecast::set_cost_bits(a[3],0x7f7fffff);auto original=bits(a);QueryCostFrame f(a,1,1,{{0,0,routecast::cost_bits(2.f)}});{auto s=f.scoped(1,0,1);assert(a[0]==1.f);}assert(bits(a)==original); }
    { std::vector<float> a{2.f},b{2.f};QueryCostFrame x(a,1,1,{{0,0,routecast::cost_bits(2.f)}}),y(b,1,1,{{0,0,routecast::cost_bits(2.f)}});auto tx=x.begin(1,0,1),ty=y.begin(1,0,1);reject([&]{x.finish(ty);});assert(a[0]==1.f && x.active());x.finish(tx);y.finish(ty); }
    { std::vector<float> a{2.f};auto original=bits(a);QueryCostFrame f(a,1,1,{{0,0,routecast::cost_bits(2.f)}});try {auto s=f.scoped(1,0,1);throw std::runtime_error("simulated search exception");}catch(const std::runtime_error&){}assert(bits(a)==original && !f.active()); }
    for(auto config: {std::pair<bool,uint32_t>{false,1},{true,2}}) {
        std::vector<float> a{2.f};auto original=bits(a);QueryCostFrame f(a,1,1,{{0,0,routecast::cost_bits(2.f)}},config.first,config.second);reject([&]{f.begin(1,0,1);});assert(bits(a)==original);auto t=f.begin(1,0,2);f.finish(t);assert(bits(a)==original);
    }
    { std::vector<float> a{7.f};QueryCostFrame f(a,1,1,{},false,4);auto t=f.begin(1,0,1);f.finish(t);assert(a[0]==7.f); }
    { std::vector<float> a{2.f,3.f};reject([&]{QueryCostFrame f(a,1,1,{{0,0,routecast::cost_bits(2.f)},{0,0,routecast::cost_bits(2.f)}});});reject([&]{QueryCostFrame f(a,1,1,{{2,0,routecast::cost_bits(2.f)}});});reject([&]{QueryCostFrame f(a,1,1,{{0,1,routecast::cost_bits(2.f)}});});reject([&]{QueryCostFrame f(a,1,1,{{0,0,0x7f800000}});}); }
    std::cout<<"SYNTHETIC_PASS "<<transactions<<" "<<checks<<"\n";
}
static std::vector<float> snapshot(const std::string& path) {
    std::ifstream f(path,std::ios::binary);std::string h;std::getline(f,h);std::istringstream s(h);std::string tag;size_t n;s>>tag>>n;assert(tag=="RCACCBITS1" && n==904438);std::vector<float> a(n);f.read(reinterpret_cast<char*>(a.data()),n*4);assert(f.gcount()==std::streamsize(n*4));char extra;assert(!f.get(extra));return a;
}
static void real_snapshot(const char* initial_path,const char* after_path,const char* claims_path) {
    auto costs=snapshot(initial_path),after=snapshot(after_path);const auto original=costs;auto expected=costs;
    std::ifstream input(claims_path);std::string tag;size_t n,count;uint32_t nets;uint64_t epoch;input>>tag>>n>>nets>>epoch>>count;assert(tag=="COSTCLAIM1" && n==costs.size() && epoch==1);std::vector<Claim> claims;
    for(size_t i=0;i<count;++i) {uint64_t node,net,b;assert(bool(input>>node>>net>>b));assert(node<=UINT32_MAX && net<=UINT32_MAX && b<=UINT32_MAX);claims.push_back({uint32_t(node),uint32_t(net),uint32_t(b)});}
    std::string extra;assert(!(input>>extra));QueryCostFrame f(costs,nets,epoch,claims);size_t applied=0,nonempty=0;
    for(uint32_t net=0;net<nets;++net) {
        for(const auto& c:f.claims_for(net))routecast::set_cost_bits(expected[c.node],QueryCostFrame::one_bits);
        auto t=f.begin(epoch,net,1);
        if(!f.claims_for(net).empty()) {assert(std::memcmp(costs.data(),expected.data(),n*4)==0);++nonempty;}
        for(const auto& c:f.claims_for(net)) {routecast::set_cost_bits(expected[c.node],c.hint_bits);++applied;}
        f.finish(t);if(!f.claims_for(net).empty())assert(std::memcmp(costs.data(),original.data(),n*4)==0);
    }
    assert(applied==count && std::memcmp(costs.data(),original.data(),n*4)==0);costs=after;
    for(uint32_t net=0;net<nets;++net) {auto t=f.begin(epoch,net,2);f.finish(t);}
    assert(std::memcmp(costs.data(),after.data(),n*4)==0);
    if(!claims.empty()) {reject([&]{f.begin(epoch,claims.front().net,1);});assert(std::memcmp(costs.data(),after.data(),n*4)==0);}
    std::cout<<"REAL_SNAPSHOT_PASS "<<n<<" "<<nets<<" "<<count<<" "<<nonempty<<"\n";
}
int main(int argc,char** argv) {
    static_assert(sizeof(float)==4 && std::numeric_limits<float>::is_iec559,"binary32 required");
    if(argc==5 && std::string(argv[1])=="--snapshot") {real_snapshot(argv[2],argv[3],argv[4]);return 0;}
    if(argc==2 && std::string(argv[1])=="--unexpected-history") {
        std::vector<float> a{2.f,4.f};QueryCostFrame f(a,1,1,{{0,0,routecast::cost_bits(2.f)},{1,0,routecast::cost_bits(4.f)}});auto t=f.begin(1,0,1);a[1]=1.5f;auto altered=bits(a);reject([&]{f.finish(t);});assert(bits(a)==altered && f.active());reject([&]{f.begin(1,0,1);});assert(bits(a)==altered);std::cout<<"UNEXPECTED_HISTORY_PRESERVED_FAIL_CLOSED\n"<<std::flush;std::_Exit(86);
    }
    if(argc==2 && (std::string(argv[1])=="--leak-frame" || std::string(argv[1])=="--raii-history")) {
        std::set_terminate([]{std::_Exit(87);});std::vector<float> a{2.f};QueryCostFrame f(a,1,1,{{0,0,routecast::cost_bits(2.f)}});
        if(std::string(argv[1])=="--leak-frame") {f.begin(1,0,1);std::cout<<"ACTIVE_FRAME_LEAK_ARMED\n"<<std::flush;return 0;}
        {auto s=f.scoped(1,0,1);a[0]=1.5f;std::cout<<"SCOPED_UNEXPECTED_HISTORY_ARMED\n"<<std::flush;}
        return 1;
    }
    synthetic();return 0;
}
